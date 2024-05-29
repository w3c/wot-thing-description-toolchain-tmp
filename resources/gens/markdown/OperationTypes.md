
# Enum: OperationTypes

Enumerations of well-known operation types necessary to implement the WoT interaction model.

URI: [td:OperationTypes](https://www.w3.org/2019/wot/td#OperationTypes)


## Permissible Values

| Text | Description | Meaning | Other Information |
| :--- | :---: | :---: | ---: |
| readproperty | Identifies the read operation on Property Affordances to retrieve the corresponding data. | td:readProperty |  |
| writeproperty | Identifies the write operation on Property Affordances to update the corresponding data. | td:writeProperty |  |
| observeproperty | Identifies the observe operation on Property Affordances to be notified with the new data when the Property is updated. | td:observeProperty |  |
| unobserveproperty | Identifies the unobserve operation on Property Affordances to stop the corresponding notifications. | td:unobserveProperty |  |
| invokeaction | Identifies the invoke operation on Action Affordances to perform the corresponding action. | td:invokeAction |  |
| queryaction | Identifies the querying operation on Action Affordances to get the status of the corresponding action. | td:queryAction |  |
| cancelaction | Identifies the cancel operation on Action Affordances to cancel the ongoing corresponding action. | td:cancelAction |  |
| subscribeevent | Identifies the subscribe operation on Event Affordances to be notified by the Thing when the event occurs. | td:subscribeEvent |  |
| unsubscribeevent | Identifies the unsubscribe operation on Event Affordances to stop the corresponding notifications. | td:unsubscribeEvent |  |
| readallproperties | Identifies the readallproperties operation on a Thing to retrieve the data of all Properties in a single interaction. | td:readAllProperties |  |
| writeallproperties | Identifies the writeallproperties operation on a Thing to update the data of all writable Properties in a single interaction. | writeAllProperties |  |
| readmultipleproperties | Identifies the readmultipleproperties operation on a Thing to retrieve the data of selected Properties in a single interaction. | td:readMultipleProperties |  |
| writemultipleproperties | Identifies the writemultipleproperties operation on a Thing to update the data of selected writable Properties in a single interaction. | td:writeMultipleProperties |  |
| observeallproperties | Identifies the observeallproperties operation on Properties to be notified with new data when any Property is updated. | td:observeAllProperties |  |
| unobserveallproperties | Identifies the unobserveallproperties operation on Properties to stop notifications from all Properties in a single interaction. | td:unobserveAllProperties |  |
| subscribeallevents | Identifies the subscribeallevents operation on Events to subscribe to notifications from all Events in a single interaction. | td:subscribeAllEvents |  |
| unsubscribeallevents | Identifies the unsubscribeallevents operation on Events to unsubscribe from notifications from all Events in a single interaction. | td:unsubscribeAllEvents |  |
| queryallactions | Identifies the queryallactions operation on a Thing to get the status of all Actions in a single interaction. | td:queryAllActions |  |

