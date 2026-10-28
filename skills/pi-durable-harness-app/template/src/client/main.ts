// FoldKit client: The Elm Architecture on Effect. The Model holds only what the host last sent
// (the projection) plus connection and in-flight command ids. Buttons come from the shared
// `actionsFor`, the same function the host uses to refuse stale intents.
import { Duration, Effect, Match, Option, Queue, Schema, Stream } from 'effect'
import { Command, ManagedResource, Runtime, Subscription, type Update } from 'foldkit'
import { type Document, type Html, type HtmlBuilder } from 'foldkit/html'
import { defineMessageUnion } from 'foldkit/message'
import { defineTaggedUnion } from 'foldkit/schema'
import { modifyFields } from 'foldkit/struct'

import { actionsFor, HostRecord, JobView } from '../shared/protocol.ts'

// ?session=<id> picks the session (one Durable Object each on Cloudflare; ignored by the Bun host).
const RPC_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/rpc${location.search}`
const decodeRecord = Schema.decodeUnknownOption(Schema.fromJsonString(HostRecord))

// MODEL

const RpcSocket = ManagedResource.tag<WebSocket>()('RpcSocket')
type RpcSocketService = ManagedResource.ServiceOf<typeof RpcSocket>

export const Connection = defineTaggedUnion({
  Connecting: {},
  Connected: {},
  Lost: { reason: Schema.String },
})

export const Model = Schema.Struct({
  connection: Connection,
  boot: Schema.String,
  version: Schema.Number,
  jobs: Schema.Array(JobView),
  inFlight: Schema.Array(Schema.Struct({ id: Schema.String, jobId: Schema.String })),
  notice: Schema.String,
  seq: Schema.Number,
})
export type Model = typeof Model.Type

// MESSAGE

export const Message = defineMessageUnion({
  ConnectedRpcSocket: {},
  ReleasedRpcSocket: {},
  FailedConnectRpcSocket: { error: Schema.String },
  ClosedRpcSocket: {},
  ReceivedRecord: { json: Schema.String },
  ClickedAction: { command: Schema.Literals(['job.start', 'job.cancel']), jobId: Schema.String },
  CompletedSendAct: { id: Schema.String },
  FailedSendAct: { id: Schema.String, error: Schema.String },
  CompletedWaitReconnect: {},
})
export type Message = typeof Message.Type

// UPDATE

type UpdateReturn = Update.Return<Model, Message, RpcSocketService>

export const update = (model: Model, message: Message) =>
  Message.match<UpdateReturn>(message, {
    ConnectedRpcSocket: () => ({ model: modifyFields(model, { connection: () => Connection.Connected() }) }),
    ReleasedRpcSocket: () => ({ model }),
    FailedConnectRpcSocket: ({ error }) => ({
      model: modifyFields(model, { connection: () => Connection.Lost({ reason: error }) }),
      commands: [WaitReconnect({})],
    }),
    ClosedRpcSocket: () => ({
      model: modifyFields(model, { connection: () => Connection.Lost({ reason: 'Host restarting' }), inFlight: () => [] }),
      commands: [WaitReconnect({})],
    }),
    CompletedWaitReconnect: () => ({ model: modifyFields(model, { connection: () => Connection.Connecting() }) }),
    ReceivedRecord: ({ json }) =>
      Option.match(decodeRecord(json), {
        onNone: () => ({ model }),
        onSome: record =>
          Match.value(record).pipe(
            Match.withReturnType<UpdateReturn>(),
            Match.tag('view', view =>
              view.boot === model.boot && view.version <= model.version
                ? { model }
                : { model: modifyFields(model, { boot: () => view.boot, version: () => view.version, jobs: () => view.jobs }) },
            ),
            Match.tag('response', response => ({
              model: modifyFields(model, {
                inFlight: inFlight => inFlight.filter(f => f.id !== response.id),
                notice: () =>
                  response.success ? (response.duplicate ? 'Already done: that request ran once.' : '') : (response.error ?? 'Refused'),
              }),
            })),
            Match.exhaustive,
          ),
      }),
    ClickedAction: ({ command, jobId }) => {
      const id = `act-${model.seq + 1}`
      return {
        model: modifyFields(model, {
          seq: seq => seq + 1,
          inFlight: inFlight => [...inFlight, { id, jobId }],
        }),
        commands: [SendAct({ id, command, jobId })],
      }
    },
    CompletedSendAct: () => ({ model }),
    FailedSendAct: ({ id, error }) => ({
      model: modifyFields(model, { inFlight: inFlight => inFlight.filter(f => f.id !== id), notice: () => error }),
    }),
  })

// INIT

export const init: Runtime.ApplicationInit<Model, Message> = () => ({
  model: { connection: Connection.Connecting(), boot: '', version: 0, jobs: [], inFlight: [], notice: '', seq: 0 },
})

// COMMAND

export const SendAct = Command.define('SendAct', {
  args: { id: Schema.String, command: Schema.Literals(['job.start', 'job.cancel']), jobId: Schema.String },
  messages: [Message.CompletedSendAct, Message.FailedSendAct],
  execute: ({ id, command, jobId }) =>
    RpcSocket.get.pipe(
      Effect.map(socket => {
        // The requestId is the intent's idempotency key: the host applies each one once.
        const requestId = `${id}-${crypto.randomUUID()}`
        socket.send(JSON.stringify({ _tag: 'act', id, requestId, command, ...(jobId ? { jobId } : {}) }))
        return Message.CompletedSendAct({ id })
      }),
      Effect.catchTag('ResourceNotAvailable', () => Effect.succeed(Message.FailedSendAct({ id, error: 'Not connected' }))),
    ),
})

export const WaitReconnect = Command.define('WaitReconnect', {
  args: {},
  messages: [Message.CompletedWaitReconnect],
  execute: () => Effect.sleep(Duration.seconds(1)).pipe(Effect.as(Message.CompletedWaitReconnect())),
})

// MANAGED RESOURCE

export const managedResources = ManagedResource.make<Model, Message>()(entry => ({
  rpcSocket: entry(Schema.Option(Schema.Null), {
    resource: RpcSocket,
    modelToMaybeRequirements: model =>
      Connection.match(model.connection, {
        Connecting: () => Option.some(null),
        Connected: () => Option.some(null),
        Lost: () => Option.none(),
      }),
    acquire: () =>
      Effect.callback<WebSocket, Error>(resume => {
        const ws = new WebSocket(RPC_URL)
        const onOpen = () => resume(Effect.succeed(ws))
        const onError = () => resume(Effect.fail(new Error('Could not reach the host')))
        ws.addEventListener('open', onOpen, { once: true })
        ws.addEventListener('error', onError, { once: true })
        return Effect.sync(() => {
          ws.removeEventListener('open', onOpen)
          ws.removeEventListener('error', onError)
        })
      }).pipe(Effect.timeout(Duration.seconds(5)), Effect.catchTag('TimeoutError', () => Effect.fail(new Error('Timed out')))),
    release: socket => Effect.sync(() => socket.close()),
    onAcquired: () => Message.ConnectedRpcSocket(),
    onReleased: () => Message.ReleasedRpcSocket(),
    onAcquireError: error => Message.FailedConnectRpcSocket({ error: error instanceof Error ? error.message : 'Unknown error' }),
  }),
}))

// SUBSCRIPTION

const records = (socket: WebSocket) =>
  Stream.callback<typeof Message.ReceivedRecord.Type | typeof Message.ClosedRpcSocket.Type>(queue =>
    Effect.acquireRelease(
      Effect.sync(() => {
        const onMessage = (event: MessageEvent) => Queue.offerUnsafe(queue, Message.ReceivedRecord({ json: String(event.data) }))
        const onClose = () => {
          Queue.offerUnsafe(queue, Message.ClosedRpcSocket())
          Queue.endUnsafe(queue)
        }
        socket.addEventListener('message', onMessage)
        socket.addEventListener('close', onClose)
        return { onMessage, onClose }
      }),
      ({ onMessage, onClose }) =>
        Effect.sync(() => {
          socket.removeEventListener('message', onMessage)
          socket.removeEventListener('close', onClose)
        }),
    ).pipe(Effect.flatMap(() => Effect.never)),
  )

export const subscriptions = Subscription.make<Model, Message, RpcSocketService>()(entry => ({
  hostRecords: entry(
    { isConnected: Schema.Boolean },
    {
      modelToDependencies: model => ({ isConnected: model.connection._tag === 'Connected' }),
      dependenciesToStream: ({ isConnected }) =>
        Stream.when(
          Stream.unwrap(
            RpcSocket.get.pipe(
              Effect.map(records),
              Effect.catchTag('ResourceNotAvailable', () => Effect.succeed(Stream.empty)),
            ),
          ),
          Effect.sync(() => isConnected),
        ),
    },
  ),
}))

// VIEW

const STAGE_TONE: Record<JobView['stage'], string> = {
  queued: 'neutral',
  working: 'info',
  cancelling: 'warning',
  done: 'success',
  failed: 'error',
  cancelled: 'neutral',
}

export const view = (model: Model, h: HtmlBuilder<Message>): Document => {
  const busy = (jobId: string) => model.inFlight.some(f => f.jobId === jobId)
  const offline = model.connection._tag !== 'Connected'
  const button = (label: string, command: 'job.start' | 'job.cancel', jobId: string, primary: boolean): Html =>
    h.button(
      [
        h.Type('button'),
        h.Class(primary ? 'btn btn-primary' : 'btn'),
        h.Disabled(offline || busy(jobId)),
        h.OnClick(Message.ClickedAction({ command, jobId })),
      ],
      [busy(jobId) ? `${label}…` : label],
    )
  return {
    title: 'Harness app',
    body: h.main(
      [h.Class('page')],
      [
        h.header(
          [h.Class('head')],
          [
            h.h1([], ['Jobs.']),
            h.span(
              [h.Class(`pill pill-${offline ? 'warning' : 'success'}`), h.AriaLive('polite')],
              [Connection.match(model.connection, { Connecting: () => 'Connecting', Connected: () => 'Live', Lost: ({ reason }) => reason })],
            ),
          ],
        ),
        h.p([h.Class('lede')], ['Each job is a pi-durable task. Kill the server mid-job and start it again: the job resumes.']),
        h.div([h.Class('bar')], actionsFor(undefined).map(a => button(a.label, a.command, '', true))),
        model.notice ? h.p([h.Class('notice'), h.Role('status')], [model.notice]) : h.span([], []),
        h.ul(
          [h.Class('jobs')],
          model.jobs.map(job =>
            h.li(
              [h.Class('job')],
              [
                h.div(
                  [h.Class('job-text')],
                  [h.strong([], [job.label]), h.span([h.Class('meta')], [`app.job #${job.id} · ${job.detail}`])],
                ),
                h.span([h.Class(`pill pill-${STAGE_TONE[job.stage]}`)], [job.recovered ? `${job.stage} · recovered` : job.stage]),
                h.div([h.Class('job-actions')], actionsFor(job).map(a => button(a.label, a.command, job.id, false))),
              ],
            ),
          ),
        ),
      ],
    ),
  }
}
