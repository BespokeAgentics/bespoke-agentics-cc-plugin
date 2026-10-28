import { Runtime } from 'foldkit'

import { Message, Model, init, managedResources, subscriptions, update, view } from './main.ts'
import './styles.css'

Runtime.run(
  Runtime.makeApplication({
    Model,
    init,
    update,
    view,
    subscriptions,
    managedResources,
    container: document.getElementById('root'),
    devTools: { Message },
  }),
)
