# Enum: OperationTypes




_Enumerations of well-known operation types necessary to implement the WoT interaction model._



URI: [OperationTypes](OperationTypes.md)

## Permissible Values

| Value | Meaning | Description |
| --- | --- | --- |
| readproperty | td:readProperty | Identifies the read operation on Property Affordances to retrieve the corresp... |
| writeproperty | td:writeProperty | Identifies the write operation on Property Affordances to update the correspo... |
| observeproperty | td:observeProperty | Identifies the observe operation on Property Affordances to be notified with ... |
| unobserveproperty | td:unobserveProperty | Identifies the unobserve operation on Property Affordances to stop the corres... |
| invokeaction | td:invokeAction | Identifies the invoke operation on Action Affordances to perform the correspo... |
| queryaction | td:queryAction | Identifies the querying operation on Action Affordances to get the status of ... |
| cancelaction | td:cancelAction | Identifies the cancel operation on Action Affordances to cancel the ongoing c... |
| subscribeevent | td:subscribeEvent | Identifies the subscribe operation on Event Affordances to be notified by the... |
| unsubscribeevent | td:unsubscribeEvent | Identifies the unsubscribe operation on Event Affordances to stop the corresp... |
| readallproperties | td:readAllProperties | Identifies the readallproperties operation on a Thing to retrieve the data of... |
| writeallproperties | writeAllProperties | Identifies the writeallproperties operation on a Thing to update the data of ... |
| readmultipleproperties | td:readMultipleProperties | Identifies the readmultipleproperties operation on a Thing to retrieve the da... |
| writemultipleproperties | td:writeMultipleProperties | Identifies the writemultipleproperties operation on a Thing to update the dat... |
| observeallproperties | td:observeAllProperties | Identifies the observeallproperties operation on Properties to be notified wi... |
| unobserveallproperties | td:unobserveAllProperties | Identifies the unobserveallproperties operation on Properties to stop notific... |
| subscribeallevents | td:subscribeAllEvents | Identifies the subscribeallevents operation on Events to subscribe to notific... |
| unsubscribeallevents | td:unsubscribeAllEvents | Identifies the unsubscribeallevents operation on Events to unsubscribe from n... |
| queryallactions | td:queryAllActions | Identifies the queryallactions operation on a Thing to get the status of all ... |




## Slots

| Name | Description |
| ---  | --- |
| [operationType](operationType.md) | Indicates the semantic intention of performing the operation(s) described by ... |






## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: OperationTypes
description: Enumerations of well-known operation types necessary to implement the
  WoT interaction model.
from_schema: td
rank: 1000
permissible_values:
  readproperty:
    text: readproperty
    description: Identifies the read operation on Property Affordances to retrieve
      the corresponding data.
    meaning: td:readProperty
  writeproperty:
    text: writeproperty
    description: Identifies the write operation on Property Affordances to update
      the corresponding data.
    meaning: td:writeProperty
  observeproperty:
    text: observeproperty
    description: Identifies the observe operation on Property Affordances to be notified
      with the new data when the Property is updated.
    meaning: td:observeProperty
  unobserveproperty:
    text: unobserveproperty
    description: Identifies the unobserve operation on Property Affordances to stop
      the corresponding notifications.
    meaning: td:unobserveProperty
  invokeaction:
    text: invokeaction
    description: Identifies the invoke operation on Action Affordances to perform
      the corresponding action.
    meaning: td:invokeAction
  queryaction:
    text: queryaction
    description: Identifies the querying operation on Action Affordances to get the
      status of the corresponding action.
    meaning: td:queryAction
  cancelaction:
    text: cancelaction
    description: Identifies the cancel operation on Action Affordances to cancel the
      ongoing corresponding action.
    meaning: td:cancelAction
  subscribeevent:
    text: subscribeevent
    description: Identifies the subscribe operation on Event Affordances to be notified
      by the Thing when the event occurs.
    meaning: td:subscribeEvent
  unsubscribeevent:
    text: unsubscribeevent
    description: Identifies the unsubscribe operation on Event Affordances to stop
      the corresponding notifications.
    meaning: td:unsubscribeEvent
  readallproperties:
    text: readallproperties
    description: Identifies the readallproperties operation on a Thing to retrieve
      the data of all Properties in a single interaction.
    meaning: td:readAllProperties
  writeallproperties:
    text: writeallproperties
    description: Identifies the writeallproperties operation on a Thing to update
      the data of all writable Properties in a single interaction.
    meaning: writeAllProperties
  readmultipleproperties:
    text: readmultipleproperties
    description: Identifies the readmultipleproperties operation on a Thing to retrieve
      the data of selected Properties in a single interaction.
    meaning: td:readMultipleProperties
  writemultipleproperties:
    text: writemultipleproperties
    description: Identifies the writemultipleproperties operation on a Thing to update
      the data of selected writable Properties in a single interaction.
    meaning: td:writeMultipleProperties
  observeallproperties:
    text: observeallproperties
    description: Identifies the observeallproperties operation on Properties to be
      notified with new data when any Property is updated.
    meaning: td:observeAllProperties
  unobserveallproperties:
    text: unobserveallproperties
    description: Identifies the unobserveallproperties operation on Properties to
      stop notifications from all Properties in a single interaction.
    meaning: td:unobserveAllProperties
  subscribeallevents:
    text: subscribeallevents
    description: Identifies the subscribeallevents operation on Events to subscribe
      to notifications from all Events in a single interaction.
    meaning: td:subscribeAllEvents
  unsubscribeallevents:
    text: unsubscribeallevents
    description: Identifies the unsubscribeallevents operation on Events to unsubscribe
      from notifications from all Events in a single interaction.
    meaning: td:unsubscribeAllEvents
  queryallactions:
    text: queryallactions
    description: Identifies the queryallactions operation on a Thing to get the status
      of all Actions in a single interaction.
    meaning: td:queryAllActions

```
</details>
