# Auto generated from thing_description_schema.yaml by pythongen.py version: 0.0.1
# Generation date: 2024-05-22T14:37:39
# Schema: thing-description-schema
#
# id: td
# description: LinkML schema for modelling the W3C Web of Things Thing Description information model. This schema is used to generate
#   JSON Schema, SHACL shapes, and RDF.
# license: MIT

import dataclasses
import re
from jsonasobj2 import JsonObj, as_dict
from typing import Optional, List, Union, Dict, ClassVar, Any
from dataclasses import dataclass
from datetime import date, datetime
from linkml_runtime.linkml_model.meta import EnumDefinition, PermissibleValue, PvFormulaOptions

from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.metamodelcore import empty_list, empty_dict, bnode
from linkml_runtime.utils.yamlutils import YAMLRoot, extended_str, extended_float, extended_int
from linkml_runtime.utils.dataclass_extensions_376 import dataclasses_init_fn_with_kwargs
from linkml_runtime.utils.formatutils import camelcase, underscore, sfx
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from rdflib import Namespace, URIRef
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.linkml_model.types import Boolean, Datetime, String
from linkml_runtime.utils.metamodelcore import Bool, URI, XSDDateTime

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
DCT = CurieNamespace('dct', 'http://purl.org/dc/terms/')
DCTERMS = CurieNamespace('dcterms', 'http://purl.org/dc/terms/')
HCTL = CurieNamespace('hctl', 'https://www.w3.org/2019/wot/hypermedia#')
HTV = CurieNamespace('htv', 'http://www.w3.org/2011/http#')
JSONSCHEMA = CurieNamespace('jsonschema', 'https://www.w3.org/2019/wot/json-schema#')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
RDF = CurieNamespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = CurieNamespace('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
SCHEMA = CurieNamespace('schema', 'http://schema.org/')
TD = CurieNamespace('td', 'https://www.w3.org/2019/wot/td#')
TM = CurieNamespace('tm', 'https://www.w3.org/2019/wot/tm#')
WOTSEC = CurieNamespace('wotsec', 'https://www.w3.org/2019/wot/security#')
XSD = CurieNamespace('xsd', 'http://www.w3.org/2001/XMLSchema#')
DEFAULT_ = TD


# Types
class AnyUri(URI):
    """ a complete URI """
    type_class_uri = XSD["anyURI"]
    type_class_curie = "xsd:anyURI"
    type_name = "anyUri"
    type_model_uri = TD.AnyUri


# Class references
class MultiLanguageKey(extended_str):
    pass


class InteractionAffordanceName(extended_str):
    pass


class PropertyAffordanceName(InteractionAffordanceName):
    pass


class ActionAffordanceName(InteractionAffordanceName):
    pass


class EventAffordanceName(InteractionAffordanceName):
    pass


class ThingId(URI):
    pass


@dataclass
class VersionInfo(YAMLRoot):
    """
    Provides version information.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = SCHEMA["version"]
    class_class_curie: ClassVar[str] = "schema:version"
    class_name: ClassVar[str] = "VersionInfo"
    class_model_uri: ClassVar[URIRef] = TD.VersionInfo

    instance: str = None
    model: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.instance):
            self.MissingRequiredField("instance")
        if not isinstance(self.instance, str):
            self.instance = str(self.instance)

        if self.model is not None and not isinstance(self.model, str):
            self.model = str(self.model)

        super().__post_init__(**kwargs)


@dataclass
class MultiLanguage(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["MultiLanguage"]
    class_class_curie: ClassVar[str] = "td:MultiLanguage"
    class_name: ClassVar[str] = "MultiLanguage"
    class_model_uri: ClassVar[URIRef] = TD.MultiLanguage

    key: Union[str, MultiLanguageKey] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.key):
            self.MissingRequiredField("key")
        if not isinstance(self.key, MultiLanguageKey):
            self.key = MultiLanguageKey(self.key)

        super().__post_init__(**kwargs)


@dataclass
class Link(YAMLRoot):
    """
    A link can be viewed as a statement of the form link context that has a relation type resource at link target",
    where the optional target attributes may further describe the resource.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = HCTL["Link"]
    class_class_curie: ClassVar[str] = "hctl:Link"
    class_name: ClassVar[str] = "Link"
    class_model_uri: ClassVar[URIRef] = TD.Link

    target: URI = None
    hintsAtMediaType: Optional[str] = None
    type: Optional[str] = None
    relation: Optional[str] = None
    anchor: Optional[URI] = None
    sizes: Optional[str] = None
    hreflang: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.target):
            self.MissingRequiredField("target")
        if not isinstance(self.target, URI):
            self.target = URI(self.target)

        if self.hintsAtMediaType is not None and not isinstance(self.hintsAtMediaType, str):
            self.hintsAtMediaType = str(self.hintsAtMediaType)

        if self.type is not None and not isinstance(self.type, str):
            self.type = str(self.type)

        if self.relation is not None and not isinstance(self.relation, str):
            self.relation = str(self.relation)

        if self.anchor is not None and not isinstance(self.anchor, URI):
            self.anchor = URI(self.anchor)

        if self.sizes is not None and not isinstance(self.sizes, str):
            self.sizes = str(self.sizes)

        if self.hreflang is not None and not isinstance(self.hreflang, str):
            self.hreflang = str(self.hreflang)

        super().__post_init__(**kwargs)


@dataclass
class ExpectedResponse(YAMLRoot):
    """
    Communication metadata describing the expected response message for the primary response.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = HCTL["ExpectedResponse"]
    class_class_curie: ClassVar[str] = "hctl:ExpectedResponse"
    class_name: ClassVar[str] = "ExpectedResponse"
    class_model_uri: ClassVar[URIRef] = TD.ExpectedResponse

    contentType: str = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.contentType):
            self.MissingRequiredField("contentType")
        if not isinstance(self.contentType, str):
            self.contentType = str(self.contentType)

        super().__post_init__(**kwargs)


@dataclass
class AdditionalExpectedResponse(ExpectedResponse):
    """
    Communication metadata describing the expected response message for additional responses.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = HCTL["AdditionalExpectedResponse"]
    class_class_curie: ClassVar[str] = "hctl:AdditionalExpectedResponse"
    class_name: ClassVar[str] = "AdditionalExpectedResponse"
    class_model_uri: ClassVar[URIRef] = TD.AdditionalExpectedResponse

    contentType: str = None
    additionalOutputSchema: Optional[str] = None
    success: Optional[Union[bool, Bool]] = None
    schema: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.additionalOutputSchema is not None and not isinstance(self.additionalOutputSchema, str):
            self.additionalOutputSchema = str(self.additionalOutputSchema)

        if self.success is not None and not isinstance(self.success, Bool):
            self.success = Bool(self.success)

        if self.schema is not None and not isinstance(self.schema, str):
            self.schema = str(self.schema)

        super().__post_init__(**kwargs)


@dataclass
class Form(YAMLRoot):
    """
    A form can be viewed as a statement of to perform an operation type on form context, make a request method to
    submission target, where the optional form fields may further describe the required request. In Thing
    Descriptions, the form context is the surrounding Object, such as Properties, Actions, and Events or the Thing
    itself for meta-interactions.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = HCTL["Form"]
    class_class_curie: ClassVar[str] = "hctl:Form"
    class_name: ClassVar[str] = "Form"
    class_model_uri: ClassVar[URIRef] = TD.Form

    target: URI = None
    href: URI = None
    contentType: Optional[str] = None
    contentCoding: Optional[str] = None
    securityDefinitions: Optional[str] = None
    scopes: Optional[str] = None
    returns: Optional[Union[dict, ExpectedResponse]] = None
    additionalReturns: Optional[Union[Union[dict, AdditionalExpectedResponse], List[Union[dict, AdditionalExpectedResponse]]]] = empty_list()
    subprotocol: Optional[str] = None
    operationType: Optional[Union[Union[str, "OperationTypes"], List[Union[str, "OperationTypes"]]]] = empty_list()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.target):
            self.MissingRequiredField("target")
        if not isinstance(self.target, URI):
            self.target = URI(self.target)

        if self._is_empty(self.href):
            self.MissingRequiredField("href")
        if not isinstance(self.href, URI):
            self.href = URI(self.href)

        if self.contentType is not None and not isinstance(self.contentType, str):
            self.contentType = str(self.contentType)

        if self.contentCoding is not None and not isinstance(self.contentCoding, str):
            self.contentCoding = str(self.contentCoding)

        if self.securityDefinitions is not None and not isinstance(self.securityDefinitions, str):
            self.securityDefinitions = str(self.securityDefinitions)

        if self.scopes is not None and not isinstance(self.scopes, str):
            self.scopes = str(self.scopes)

        if self.returns is not None and not isinstance(self.returns, ExpectedResponse):
            self.returns = ExpectedResponse(**as_dict(self.returns))

        self._normalize_inlined_as_dict(slot_name="additionalReturns", slot_type=AdditionalExpectedResponse, key_name="contentType", keyed=False)

        if self.subprotocol is not None and not isinstance(self.subprotocol, str):
            self.subprotocol = str(self.subprotocol)

        if not isinstance(self.operationType, list):
            self.operationType = [self.operationType] if self.operationType is not None else []
        self.operationType = [v if isinstance(v, OperationTypes) else OperationTypes(v) for v in self.operationType]

        super().__post_init__(**kwargs)


@dataclass
class SecurityScheme(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["SecurityScheme"]
    class_class_curie: ClassVar[str] = "td:SecurityScheme"
    class_name: ClassVar[str] = "SecurityScheme"
    class_model_uri: ClassVar[URIRef] = TD.SecurityScheme

    scheme: Union[str, "SecuritySchemeType"] = None
    @type: Optional[Union[str, List[str]]] = empty_list()
    descriptions: Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]] = empty_dict()
    description: Optional[str] = None
    proxy: Optional[URI] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.scheme):
            self.MissingRequiredField("scheme")
        if not isinstance(self.scheme, SecuritySchemeType):
            self.scheme = SecuritySchemeType(self.scheme)

        if not isinstance(self.@type, list):
            self.@type = [self.@type] if self.@type is not None else []
        self.@type = [v if isinstance(v, str) else str(v) for v in self.@type]

        self._normalize_inlined_as_dict(slot_name="descriptions", slot_type=MultiLanguage, key_name="key", keyed=True)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.proxy is not None and not isinstance(self.proxy, URI):
            self.proxy = URI(self.proxy)

        super().__post_init__(**kwargs)


@dataclass
class DataSchema(YAMLRoot):
    """
    Metadata that describes the data format used. It can be used for validation.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = JSONSCHEMA["DataSchema"]
    class_class_curie: ClassVar[str] = "jsonschema:DataSchema"
    class_name: ClassVar[str] = "DataSchema"
    class_model_uri: ClassVar[URIRef] = TD.DataSchema

    description: Optional[Union[str, MultiLanguageKey]] = None
    title: Optional[Union[str, MultiLanguageKey]] = None
    titleInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    descriptionInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    propertyName: Optional[str] = None
    writeOnly: Optional[str] = None
    readonly: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.description is not None and not isinstance(self.description, MultiLanguageKey):
            self.description = MultiLanguageKey(self.description)

        if self.title is not None and not isinstance(self.title, MultiLanguageKey):
            self.title = MultiLanguageKey(self.title)

        if self.titleInLanguage is not None and not isinstance(self.titleInLanguage, MultiLanguageKey):
            self.titleInLanguage = MultiLanguageKey(self.titleInLanguage)

        if self.descriptionInLanguage is not None and not isinstance(self.descriptionInLanguage, MultiLanguageKey):
            self.descriptionInLanguage = MultiLanguageKey(self.descriptionInLanguage)

        if self.propertyName is not None and not isinstance(self.propertyName, str):
            self.propertyName = str(self.propertyName)

        if self.writeOnly is not None and not isinstance(self.writeOnly, str):
            self.writeOnly = str(self.writeOnly)

        if self.readonly is not None and not isinstance(self.readonly, str):
            self.readonly = str(self.readonly)

        super().__post_init__(**kwargs)


@dataclass
class InteractionAffordance(YAMLRoot):
    """
    TOOD
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["InteractionAffordance"]
    class_class_curie: ClassVar[str] = "td:InteractionAffordance"
    class_name: ClassVar[str] = "InteractionAffordance"
    class_model_uri: ClassVar[URIRef] = TD.InteractionAffordance

    name: Union[str, InteractionAffordanceName] = None
    titles: Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]] = empty_dict()
    descriptions: Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]] = empty_dict()
    title: Optional[Union[str, MultiLanguageKey]] = None
    description: Optional[Union[str, MultiLanguageKey]] = None
    titleInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    descriptionInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    uriVariables: Optional[Union[Union[dict, DataSchema], List[Union[dict, DataSchema]]]] = empty_list()
    forms: Optional[Union[Union[dict, Form], List[Union[dict, Form]]]] = empty_list()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, InteractionAffordanceName):
            self.name = InteractionAffordanceName(self.name)

        self._normalize_inlined_as_dict(slot_name="titles", slot_type=MultiLanguage, key_name="key", keyed=True)

        self._normalize_inlined_as_dict(slot_name="descriptions", slot_type=MultiLanguage, key_name="key", keyed=True)

        if self.title is not None and not isinstance(self.title, MultiLanguageKey):
            self.title = MultiLanguageKey(self.title)

        if self.description is not None and not isinstance(self.description, MultiLanguageKey):
            self.description = MultiLanguageKey(self.description)

        if self.titleInLanguage is not None and not isinstance(self.titleInLanguage, MultiLanguageKey):
            self.titleInLanguage = MultiLanguageKey(self.titleInLanguage)

        if self.descriptionInLanguage is not None and not isinstance(self.descriptionInLanguage, MultiLanguageKey):
            self.descriptionInLanguage = MultiLanguageKey(self.descriptionInLanguage)

        if not isinstance(self.uriVariables, list):
            self.uriVariables = [self.uriVariables] if self.uriVariables is not None else []
        self.uriVariables = [v if isinstance(v, DataSchema) else DataSchema(**as_dict(v)) for v in self.uriVariables]

        self._normalize_inlined_as_dict(slot_name="forms", slot_type=Form, key_name="target", keyed=False)

        super().__post_init__(**kwargs)


@dataclass
class PropertyAffordance(InteractionAffordance):
    """
    An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["PropertyAffordance"]
    class_class_curie: ClassVar[str] = "td:PropertyAffordance"
    class_name: ClassVar[str] = "PropertyAffordance"
    class_model_uri: ClassVar[URIRef] = TD.PropertyAffordance

    name: Union[str, PropertyAffordanceName] = None
    title: Optional[Union[str, MultiLanguageKey]] = None
    description: Optional[Union[str, MultiLanguageKey]] = None
    titleInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    descriptionInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    observable: Optional[Union[bool, Bool]] = None
    propertyName: Optional[str] = None
    writeOnly: Optional[str] = None
    readonly: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, PropertyAffordanceName):
            self.name = PropertyAffordanceName(self.name)

        if self.title is not None and not isinstance(self.title, MultiLanguageKey):
            self.title = MultiLanguageKey(self.title)

        if self.description is not None and not isinstance(self.description, MultiLanguageKey):
            self.description = MultiLanguageKey(self.description)

        if self.titleInLanguage is not None and not isinstance(self.titleInLanguage, MultiLanguageKey):
            self.titleInLanguage = MultiLanguageKey(self.titleInLanguage)

        if self.descriptionInLanguage is not None and not isinstance(self.descriptionInLanguage, MultiLanguageKey):
            self.descriptionInLanguage = MultiLanguageKey(self.descriptionInLanguage)

        if self.observable is not None and not isinstance(self.observable, Bool):
            self.observable = Bool(self.observable)

        if self.propertyName is not None and not isinstance(self.propertyName, str):
            self.propertyName = str(self.propertyName)

        if self.writeOnly is not None and not isinstance(self.writeOnly, str):
            self.writeOnly = str(self.writeOnly)

        if self.readonly is not None and not isinstance(self.readonly, str):
            self.readonly = str(self.readonly)

        super().__post_init__(**kwargs)


@dataclass
class ActionAffordance(InteractionAffordance):
    """
    An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a
    lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["ActionAffordance"]
    class_class_curie: ClassVar[str] = "td:ActionAffordance"
    class_name: ClassVar[str] = "ActionAffordance"
    class_model_uri: ClassVar[URIRef] = TD.ActionAffordance

    name: Union[str, ActionAffordanceName] = None
    safe: Optional[Union[bool, Bool]] = None
    synchronous: Optional[Union[bool, Bool]] = None
    idempotent: Optional[Union[bool, Bool]] = None
    input: Optional[Union[dict, DataSchema]] = None
    output: Optional[Union[dict, DataSchema]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, ActionAffordanceName):
            self.name = ActionAffordanceName(self.name)

        if self.safe is not None and not isinstance(self.safe, Bool):
            self.safe = Bool(self.safe)

        if self.synchronous is not None and not isinstance(self.synchronous, Bool):
            self.synchronous = Bool(self.synchronous)

        if self.idempotent is not None and not isinstance(self.idempotent, Bool):
            self.idempotent = Bool(self.idempotent)

        if self.input is not None and not isinstance(self.input, DataSchema):
            self.input = DataSchema(**as_dict(self.input))

        if self.output is not None and not isinstance(self.output, DataSchema):
            self.output = DataSchema(**as_dict(self.output))

        super().__post_init__(**kwargs)


@dataclass
class EventAffordance(InteractionAffordance):
    """
    An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers
    (e.g., overhearing alerts).
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["EventAffordance"]
    class_class_curie: ClassVar[str] = "td:EventAffordance"
    class_name: ClassVar[str] = "EventAffordance"
    class_model_uri: ClassVar[URIRef] = TD.EventAffordance

    name: Union[str, EventAffordanceName] = None
    subscription: Optional[Union[dict, DataSchema]] = None
    cancellation: Optional[Union[dict, DataSchema]] = None
    notification: Optional[Union[dict, DataSchema]] = None
    notificationResponse: Optional[Union[dict, DataSchema]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, EventAffordanceName):
            self.name = EventAffordanceName(self.name)

        if self.subscription is not None and not isinstance(self.subscription, DataSchema):
            self.subscription = DataSchema(**as_dict(self.subscription))

        if self.cancellation is not None and not isinstance(self.cancellation, DataSchema):
            self.cancellation = DataSchema(**as_dict(self.cancellation))

        if self.notification is not None and not isinstance(self.notification, DataSchema):
            self.notification = DataSchema(**as_dict(self.notification))

        if self.notificationResponse is not None and not isinstance(self.notificationResponse, DataSchema):
            self.notificationResponse = DataSchema(**as_dict(self.notificationResponse))

        super().__post_init__(**kwargs)


@dataclass
class Thing(YAMLRoot):
    """
    An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing
    Description, whereas a virtual entity is the composition of one or more Things.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TD["Thing"]
    class_class_curie: ClassVar[str] = "td:Thing"
    class_name: ClassVar[str] = "Thing"
    class_model_uri: ClassVar[URIRef] = TD.Thing

    id: Union[URI, ThingId] = None
    title: Optional[Union[str, MultiLanguageKey]] = None
    description: Optional[Union[str, MultiLanguageKey]] = None
    titles: Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]] = empty_dict()
    descriptions: Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]] = empty_dict()
    @type: Optional[Union[str, List[str]]] = empty_list()
    titleInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    descriptionInLanguage: Optional[Union[str, MultiLanguageKey]] = None
    securityDefinitions: Optional[Union[str, List[str]]] = empty_list()
    security: Optional[Union[str, List[str]]] = empty_list()
    schemaDefinitions: Optional[Union[Union[dict, DataSchema], List[Union[dict, DataSchema]]]] = empty_list()
    profile: Optional[Union[URI, List[URI]]] = empty_list()
    instance: Optional[str] = None
    created: Optional[Union[str, XSDDateTime]] = None
    modified: Optional[Union[str, XSDDateTime]] = None
    supportContact: Optional[URI] = None
    base: Optional[URI] = None
    version: Optional[Union[dict, VersionInfo]] = None
    forms: Optional[Union[Union[dict, Form], List[Union[dict, Form]]]] = empty_list()
    links: Optional[Union[Union[dict, Link], List[Union[dict, Link]]]] = empty_list()
    properties: Optional[Union[Dict[Union[str, PropertyAffordanceName], Union[dict, PropertyAffordance]], List[Union[dict, PropertyAffordance]]]] = empty_dict()
    actions: Optional[Union[Dict[Union[str, ActionAffordanceName], Union[dict, ActionAffordance]], List[Union[dict, ActionAffordance]]]] = empty_dict()
    events: Optional[Union[Dict[Union[str, EventAffordanceName], Union[dict, EventAffordance]], List[Union[dict, EventAffordance]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ThingId):
            self.id = ThingId(self.id)

        if self.title is not None and not isinstance(self.title, MultiLanguageKey):
            self.title = MultiLanguageKey(self.title)

        if self.description is not None and not isinstance(self.description, MultiLanguageKey):
            self.description = MultiLanguageKey(self.description)

        self._normalize_inlined_as_dict(slot_name="titles", slot_type=MultiLanguage, key_name="key", keyed=True)

        self._normalize_inlined_as_dict(slot_name="descriptions", slot_type=MultiLanguage, key_name="key", keyed=True)

        if not isinstance(self.@type, list):
            self.@type = [self.@type] if self.@type is not None else []
        self.@type = [v if isinstance(v, str) else str(v) for v in self.@type]

        if self.titleInLanguage is not None and not isinstance(self.titleInLanguage, MultiLanguageKey):
            self.titleInLanguage = MultiLanguageKey(self.titleInLanguage)

        if self.descriptionInLanguage is not None and not isinstance(self.descriptionInLanguage, MultiLanguageKey):
            self.descriptionInLanguage = MultiLanguageKey(self.descriptionInLanguage)

        if not isinstance(self.securityDefinitions, list):
            self.securityDefinitions = [self.securityDefinitions] if self.securityDefinitions is not None else []
        self.securityDefinitions = [v if isinstance(v, str) else str(v) for v in self.securityDefinitions]

        if not isinstance(self.security, list):
            self.security = [self.security] if self.security is not None else []
        self.security = [v if isinstance(v, str) else str(v) for v in self.security]

        if not isinstance(self.schemaDefinitions, list):
            self.schemaDefinitions = [self.schemaDefinitions] if self.schemaDefinitions is not None else []
        self.schemaDefinitions = [v if isinstance(v, DataSchema) else DataSchema(**as_dict(v)) for v in self.schemaDefinitions]

        if not isinstance(self.profile, list):
            self.profile = [self.profile] if self.profile is not None else []
        self.profile = [v if isinstance(v, URI) else URI(v) for v in self.profile]

        if self.instance is not None and not isinstance(self.instance, str):
            self.instance = str(self.instance)

        if self.created is not None and not isinstance(self.created, XSDDateTime):
            self.created = XSDDateTime(self.created)

        if self.modified is not None and not isinstance(self.modified, XSDDateTime):
            self.modified = XSDDateTime(self.modified)

        if self.supportContact is not None and not isinstance(self.supportContact, URI):
            self.supportContact = URI(self.supportContact)

        if self.base is not None and not isinstance(self.base, URI):
            self.base = URI(self.base)

        if self.version is not None and not isinstance(self.version, VersionInfo):
            self.version = VersionInfo(**as_dict(self.version))

        self._normalize_inlined_as_dict(slot_name="forms", slot_type=Form, key_name="target", keyed=False)

        self._normalize_inlined_as_dict(slot_name="links", slot_type=Link, key_name="target", keyed=False)

        self._normalize_inlined_as_dict(slot_name="properties", slot_type=PropertyAffordance, key_name="name", keyed=True)

        self._normalize_inlined_as_dict(slot_name="actions", slot_type=ActionAffordance, key_name="name", keyed=True)

        self._normalize_inlined_as_dict(slot_name="events", slot_type=EventAffordance, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


# Enumerations
class OperationTypes(EnumDefinitionImpl):
    """
    Enumerations of well-known operation types necessary to implement the WoT interaction model.
    """
    readproperty = PermissibleValue(
        text="readproperty",
        description="Identifies the read operation on Property Affordances to retrieve the corresponding data.",
        meaning=TD["readProperty"])
    writeproperty = PermissibleValue(
        text="writeproperty",
        description="Identifies the write operation on Property Affordances to update the corresponding data.",
        meaning=TD["writeProperty"])
    observeproperty = PermissibleValue(
        text="observeproperty",
        description="""Identifies the observe operation on Property Affordances to be notified with the new data when the Property is updated.""",
        meaning=TD["observeProperty"])
    unobserveproperty = PermissibleValue(
        text="unobserveproperty",
        description="""Identifies the unobserve operation on Property Affordances to stop the corresponding notifications.""",
        meaning=TD["unobserveProperty"])
    invokeaction = PermissibleValue(
        text="invokeaction",
        description="Identifies the invoke operation on Action Affordances to perform the corresponding action.",
        meaning=TD["invokeAction"])
    queryaction = PermissibleValue(
        text="queryaction",
        description="""Identifies the querying operation on Action Affordances to get the status of the corresponding action.""",
        meaning=TD["queryAction"])
    cancelaction = PermissibleValue(
        text="cancelaction",
        description="""Identifies the cancel operation on Action Affordances to cancel the ongoing corresponding action.""",
        meaning=TD["cancelAction"])
    subscribeevent = PermissibleValue(
        text="subscribeevent",
        description="""Identifies the subscribe operation on Event Affordances to be notified by the Thing when the event occurs.""",
        meaning=TD["subscribeEvent"])
    unsubscribeevent = PermissibleValue(
        text="unsubscribeevent",
        description="""Identifies the unsubscribe operation on Event Affordances to stop the corresponding notifications.""",
        meaning=TD["unsubscribeEvent"])
    readallproperties = PermissibleValue(
        text="readallproperties",
        description="""Identifies the readallproperties operation on a Thing to retrieve the data of all Properties in a single interaction.""",
        meaning=TD["readAllProperties"])
    writeallproperties = PermissibleValue(
        text="writeallproperties",
        description="""Identifies the writeallproperties operation on a Thing to update the data of all writable Properties in a single interaction.""",
        meaning=TD["writeAllProperties"])
    readmultipleproperties = PermissibleValue(
        text="readmultipleproperties",
        description="""Identifies the readmultipleproperties operation on a Thing to retrieve the data of selected Properties in a single interaction.""",
        meaning=TD["readMultipleProperties"])
    writemultipleproperties = PermissibleValue(
        text="writemultipleproperties",
        description="""Identifies the writemultipleproperties operation on a Thing to update the data of selected writable Properties in a single interaction.""",
        meaning=TD["writeMultipleProperties"])
    observeallproperties = PermissibleValue(
        text="observeallproperties",
        description="""Identifies the observeallproperties operation on Properties to be notified with new data when any Property is updated.""",
        meaning=TD["observeAllProperties"])
    unobserveallproperties = PermissibleValue(
        text="unobserveallproperties",
        description="""Identifies the unobserveallproperties operation on Properties to stop notifications from all Properties in a single interaction.""",
        meaning=TD["unobserveAllProperties"])
    subscribeallevents = PermissibleValue(
        text="subscribeallevents",
        description="""Identifies the subscribeallevents operation on Events to subscribe to notifications from all Events in a single interaction.""",
        meaning=TD["subscribeAllEvents"])
    unsubscribeallevents = PermissibleValue(
        text="unsubscribeallevents",
        description="""Identifies the unsubscribeallevents operation on Events to unsubscribe from notifications from all Events in a single interaction.""",
        meaning=TD["unsubscribeAllEvents"])
    queryallactions = PermissibleValue(
        text="queryallactions",
        description="""Identifies the queryallactions operation on a Thing to get the status of all Actions in a single interaction.""",
        meaning=TD["queryAllActions"])

    _defn = EnumDefinition(
        name="OperationTypes",
        description="Enumerations of well-known operation types necessary to implement the WoT interaction model.",
    )

class SecuritySchemeType(EnumDefinitionImpl):

    nosec = PermissibleValue(
        text="nosec",
        description="""A security configuration corresponding to identified by the Vocabulary Term nosec, indicating there is no authentication or other mechanism required to access the resource.""",
        meaning=WOTSEC["NoSecurityScheme"])
    combo = PermissibleValue(
        text="combo",
        description="""Elements of this scheme define various ways in which other named schemes defined in securityDefinitions, including other ComboSecurityScheme definitions, are to be combined to create a new scheme definition.""",
        meaning=WOTSEC["ComboSecurityScheme"])
    basic = PermissibleValue(
        text="basic",
        description="Uses an unencrypted username and password.",
        meaning=WOTSEC["BasicSecurityScheme"])
    digest = PermissibleValue(
        text="digest",
        description="""This scheme is similar to basic authentication but with added features to avoid man-in-the-middle attacks.""",
        meaning=WOTSEC["DigestSecurityScheme"])
    bearer = PermissibleValue(
        text="bearer",
        description="Bearer tokens are used independently of OAuth2.",
        meaning=WOTSEC["BearerSecurityScheme"])
    psk = PermissibleValue(
        text="psk",
        description="""This is meant to identify that a standard is used for pre-shared keys such as TLS-PSK [RFC4279], and that the ciphersuite used for keys will be established during protocol negotiation.""",
        meaning=WOTSEC["PSKSecurityScheme"])
    oauth2 = PermissibleValue(
        text="oauth2",
        description="""OAuth 2.0 authentication security configuration for systems conformant with [RFC6749] and [RFC8252].""",
        meaning=WOTSEC["OAuth2SecurityScheme"])
    apikey = PermissibleValue(
        text="apikey",
        description="This scheme is to be used when the access token is opaque.",
        meaning=WOTSEC["APIKeySecurityScheme"])
    auto = PermissibleValue(
        text="auto",
        description="""This scheme indicates that the security parameters are going to be negotiated by the underlying protocols at runtime""",
        meaning=WOTSEC["AutoSecurityScheme"])

    _defn = EnumDefinition(
        name="SecuritySchemeType",
    )

# Slots
class slots:
    pass

slots.id = Slot(uri=TD.id, name="id", curie=TD.curie('id'),
                   model_uri=TD.id, domain=None, range=URIRef)

slots.title = Slot(uri=TD.title, name="title", curie=TD.curie('title'),
                   model_uri=TD.title, domain=None, range=Optional[Union[str, MultiLanguageKey]])

slots.description = Slot(uri=TD.description, name="description", curie=TD.curie('description'),
                   model_uri=TD.description, domain=None, range=Optional[Union[str, MultiLanguageKey]])

slots.titles = Slot(uri=TD.titles, name="titles", curie=TD.curie('titles'),
                   model_uri=TD.titles, domain=None, range=Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]])

slots.descriptions = Slot(uri=TD.descriptions, name="descriptions", curie=TD.curie('descriptions'),
                   model_uri=TD.descriptions, domain=None, range=Optional[Union[List[Union[str, MultiLanguageKey]], Dict[Union[str, MultiLanguageKey], Union[dict, MultiLanguage]]]])

slots.descriptionInLanguage = Slot(uri=TD.descriptionInLanguage, name="descriptionInLanguage", curie=TD.curie('descriptionInLanguage'),
                   model_uri=TD.descriptionInLanguage, domain=None, range=Optional[Union[str, MultiLanguageKey]])

slots.titleInLanguage = Slot(uri=TD.titleInLanguage, name="titleInLanguage", curie=TD.curie('titleInLanguage'),
                   model_uri=TD.titleInLanguage, domain=None, range=Optional[Union[str, MultiLanguageKey]])

slots.@type = Slot(uri=TD['@type'], name="@type", curie=TD.curie('@type'),
                   model_uri=TD['@type'], domain=None, range=Optional[Union[str, List[str]]])

slots.target = Slot(uri=HCTL.target, name="target", curie=HCTL.curie('target'),
                   model_uri=TD.target, domain=None, range=URI)

slots.versionInfo__instance = Slot(uri=TD.instance, name="versionInfo__instance", curie=TD.curie('instance'),
                   model_uri=TD.versionInfo__instance, domain=None, range=str)

slots.versionInfo__model = Slot(uri=TD.model, name="versionInfo__model", curie=TD.curie('model'),
                   model_uri=TD.versionInfo__model, domain=None, range=Optional[str])

slots.multiLanguage__key = Slot(uri=TD.key, name="multiLanguage__key", curie=TD.curie('key'),
                   model_uri=TD.multiLanguage__key, domain=None, range=URIRef,
                   pattern=re.compile(r'^(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+)|((en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)|(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)))$'))

slots.link__hintsAtMediaType = Slot(uri=TD.hintsAtMediaType, name="link__hintsAtMediaType", curie=TD.curie('hintsAtMediaType'),
                   model_uri=TD.link__hintsAtMediaType, domain=None, range=Optional[str])

slots.link__type = Slot(uri=TD.type, name="link__type", curie=TD.curie('type'),
                   model_uri=TD.link__type, domain=None, range=Optional[str])

slots.link__relation = Slot(uri=TD.relation, name="link__relation", curie=TD.curie('relation'),
                   model_uri=TD.link__relation, domain=None, range=Optional[str])

slots.link__anchor = Slot(uri=TD.anchor, name="link__anchor", curie=TD.curie('anchor'),
                   model_uri=TD.link__anchor, domain=None, range=Optional[URI])

slots.link__sizes = Slot(uri=TD.sizes, name="link__sizes", curie=TD.curie('sizes'),
                   model_uri=TD.link__sizes, domain=None, range=Optional[str])

slots.link__hreflang = Slot(uri=TD.hreflang, name="link__hreflang", curie=TD.curie('hreflang'),
                   model_uri=TD.link__hreflang, domain=None, range=Optional[str],
                   pattern=re.compile(r'^(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+)|((en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)|(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)))$'))

slots.expectedResponse__contentType = Slot(uri=TD.contentType, name="expectedResponse__contentType", curie=TD.curie('contentType'),
                   model_uri=TD.expectedResponse__contentType, domain=None, range=str)

slots.additionalExpectedResponse__additionalOutputSchema = Slot(uri=TD.additionalOutputSchema, name="additionalExpectedResponse__additionalOutputSchema", curie=TD.curie('additionalOutputSchema'),
                   model_uri=TD.additionalExpectedResponse__additionalOutputSchema, domain=None, range=Optional[str])

slots.additionalExpectedResponse__success = Slot(uri=TD.success, name="additionalExpectedResponse__success", curie=TD.curie('success'),
                   model_uri=TD.additionalExpectedResponse__success, domain=None, range=Optional[Union[bool, Bool]])

slots.additionalExpectedResponse__schema = Slot(uri=TD.schema, name="additionalExpectedResponse__schema", curie=TD.curie('schema'),
                   model_uri=TD.additionalExpectedResponse__schema, domain=None, range=Optional[str])

slots.form__href = Slot(uri=TD.href, name="form__href", curie=TD.curie('href'),
                   model_uri=TD.form__href, domain=None, range=URI)

slots.form__contentType = Slot(uri=TD.contentType, name="form__contentType", curie=TD.curie('contentType'),
                   model_uri=TD.form__contentType, domain=None, range=Optional[str])

slots.form__contentCoding = Slot(uri=TD.contentCoding, name="form__contentCoding", curie=TD.curie('contentCoding'),
                   model_uri=TD.form__contentCoding, domain=None, range=Optional[str])

slots.form__securityDefinitions = Slot(uri=TD.securityDefinitions, name="form__securityDefinitions", curie=TD.curie('securityDefinitions'),
                   model_uri=TD.form__securityDefinitions, domain=None, range=Optional[str])

slots.form__scopes = Slot(uri=TD.scopes, name="form__scopes", curie=TD.curie('scopes'),
                   model_uri=TD.form__scopes, domain=None, range=Optional[str])

slots.form__returns = Slot(uri=TD.returns, name="form__returns", curie=TD.curie('returns'),
                   model_uri=TD.form__returns, domain=None, range=Optional[Union[dict, ExpectedResponse]])

slots.form__additionalReturns = Slot(uri=TD.additionalReturns, name="form__additionalReturns", curie=TD.curie('additionalReturns'),
                   model_uri=TD.form__additionalReturns, domain=None, range=Optional[Union[Union[dict, AdditionalExpectedResponse], List[Union[dict, AdditionalExpectedResponse]]]])

slots.form__subprotocol = Slot(uri=TD.subprotocol, name="form__subprotocol", curie=TD.curie('subprotocol'),
                   model_uri=TD.form__subprotocol, domain=None, range=Optional[str])

slots.form__operationType = Slot(uri=TD.operationType, name="form__operationType", curie=TD.curie('operationType'),
                   model_uri=TD.form__operationType, domain=None, range=Optional[Union[Union[str, "OperationTypes"], List[Union[str, "OperationTypes"]]]])

slots.securityScheme__description = Slot(uri=TD.description, name="securityScheme__description", curie=TD.curie('description'),
                   model_uri=TD.securityScheme__description, domain=None, range=Optional[str])

slots.securityScheme__proxy = Slot(uri=TD.proxy, name="securityScheme__proxy", curie=TD.curie('proxy'),
                   model_uri=TD.securityScheme__proxy, domain=None, range=Optional[URI])

slots.securityScheme__scheme = Slot(uri=TD.scheme, name="securityScheme__scheme", curie=TD.curie('scheme'),
                   model_uri=TD.securityScheme__scheme, domain=None, range=Union[str, "SecuritySchemeType"])

slots.dataSchema__propertyName = Slot(uri=TD.propertyName, name="dataSchema__propertyName", curie=TD.curie('propertyName'),
                   model_uri=TD.dataSchema__propertyName, domain=None, range=Optional[str])

slots.dataSchema__writeOnly = Slot(uri=TD.writeOnly, name="dataSchema__writeOnly", curie=TD.curie('writeOnly'),
                   model_uri=TD.dataSchema__writeOnly, domain=None, range=Optional[str])

slots.dataSchema__readonly = Slot(uri=TD.readonly, name="dataSchema__readonly", curie=TD.curie('readonly'),
                   model_uri=TD.dataSchema__readonly, domain=None, range=Optional[str])

slots.interactionAffordance__name = Slot(uri=TD.name, name="interactionAffordance__name", curie=TD.curie('name'),
                   model_uri=TD.interactionAffordance__name, domain=None, range=URIRef)

slots.interactionAffordance__uriVariables = Slot(uri=TD.uriVariables, name="interactionAffordance__uriVariables", curie=TD.curie('uriVariables'),
                   model_uri=TD.interactionAffordance__uriVariables, domain=None, range=Optional[Union[Union[dict, DataSchema], List[Union[dict, DataSchema]]]])

slots.interactionAffordance__forms = Slot(uri=TD.forms, name="interactionAffordance__forms", curie=TD.curie('forms'),
                   model_uri=TD.interactionAffordance__forms, domain=None, range=Optional[Union[Union[dict, Form], List[Union[dict, Form]]]])

slots.propertyAffordance__observable = Slot(uri=TD.observable, name="propertyAffordance__observable", curie=TD.curie('observable'),
                   model_uri=TD.propertyAffordance__observable, domain=None, range=Optional[Union[bool, Bool]])

slots.actionAffordance__safe = Slot(uri=TD.safe, name="actionAffordance__safe", curie=TD.curie('safe'),
                   model_uri=TD.actionAffordance__safe, domain=None, range=Optional[Union[bool, Bool]])

slots.actionAffordance__synchronous = Slot(uri=TD.synchronous, name="actionAffordance__synchronous", curie=TD.curie('synchronous'),
                   model_uri=TD.actionAffordance__synchronous, domain=None, range=Optional[Union[bool, Bool]])

slots.actionAffordance__idempotent = Slot(uri=TD.idempotent, name="actionAffordance__idempotent", curie=TD.curie('idempotent'),
                   model_uri=TD.actionAffordance__idempotent, domain=None, range=Optional[Union[bool, Bool]])

slots.actionAffordance__input = Slot(uri=TD.input, name="actionAffordance__input", curie=TD.curie('input'),
                   model_uri=TD.actionAffordance__input, domain=None, range=Optional[Union[dict, DataSchema]])

slots.actionAffordance__output = Slot(uri=TD.output, name="actionAffordance__output", curie=TD.curie('output'),
                   model_uri=TD.actionAffordance__output, domain=None, range=Optional[Union[dict, DataSchema]])

slots.eventAffordance__subscription = Slot(uri=TD.subscription, name="eventAffordance__subscription", curie=TD.curie('subscription'),
                   model_uri=TD.eventAffordance__subscription, domain=None, range=Optional[Union[dict, DataSchema]])

slots.eventAffordance__cancellation = Slot(uri=TD.cancellation, name="eventAffordance__cancellation", curie=TD.curie('cancellation'),
                   model_uri=TD.eventAffordance__cancellation, domain=None, range=Optional[Union[dict, DataSchema]])

slots.eventAffordance__notification = Slot(uri=TD.notification, name="eventAffordance__notification", curie=TD.curie('notification'),
                   model_uri=TD.eventAffordance__notification, domain=None, range=Optional[Union[dict, DataSchema]])

slots.eventAffordance__notificationResponse = Slot(uri=TD.notificationResponse, name="eventAffordance__notificationResponse", curie=TD.curie('notificationResponse'),
                   model_uri=TD.eventAffordance__notificationResponse, domain=None, range=Optional[Union[dict, DataSchema]])

slots.thing__securityDefinitions = Slot(uri=TD.securityDefinitions, name="thing__securityDefinitions", curie=TD.curie('securityDefinitions'),
                   model_uri=TD.thing__securityDefinitions, domain=None, range=Optional[Union[str, List[str]]])

slots.thing__security = Slot(uri=TD.security, name="thing__security", curie=TD.curie('security'),
                   model_uri=TD.thing__security, domain=None, range=Optional[Union[str, List[str]]])

slots.thing__schemaDefinitions = Slot(uri=TD.schemaDefinitions, name="thing__schemaDefinitions", curie=TD.curie('schemaDefinitions'),
                   model_uri=TD.thing__schemaDefinitions, domain=None, range=Optional[Union[Union[dict, DataSchema], List[Union[dict, DataSchema]]]])

slots.thing__profile = Slot(uri=TD.profile, name="thing__profile", curie=TD.curie('profile'),
                   model_uri=TD.thing__profile, domain=None, range=Optional[Union[URI, List[URI]]])

slots.thing__instance = Slot(uri=TD.instance, name="thing__instance", curie=TD.curie('instance'),
                   model_uri=TD.thing__instance, domain=None, range=Optional[str])

slots.thing__created = Slot(uri=TD.created, name="thing__created", curie=TD.curie('created'),
                   model_uri=TD.thing__created, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.thing__modified = Slot(uri=TD.modified, name="thing__modified", curie=TD.curie('modified'),
                   model_uri=TD.thing__modified, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.thing__supportContact = Slot(uri=TD.supportContact, name="thing__supportContact", curie=TD.curie('supportContact'),
                   model_uri=TD.thing__supportContact, domain=None, range=Optional[URI])

slots.thing__base = Slot(uri=TD.base, name="thing__base", curie=TD.curie('base'),
                   model_uri=TD.thing__base, domain=None, range=Optional[URI])

slots.thing__version = Slot(uri=TD.version, name="thing__version", curie=TD.curie('version'),
                   model_uri=TD.thing__version, domain=None, range=Optional[Union[dict, VersionInfo]])

slots.thing__forms = Slot(uri=TD.forms, name="thing__forms", curie=TD.curie('forms'),
                   model_uri=TD.thing__forms, domain=None, range=Optional[Union[Union[dict, Form], List[Union[dict, Form]]]])

slots.thing__links = Slot(uri=TD.links, name="thing__links", curie=TD.curie('links'),
                   model_uri=TD.thing__links, domain=None, range=Optional[Union[Union[dict, Link], List[Union[dict, Link]]]])

slots.thing__properties = Slot(uri=TD.properties, name="thing__properties", curie=TD.curie('properties'),
                   model_uri=TD.thing__properties, domain=None, range=Optional[Union[Dict[Union[str, PropertyAffordanceName], Union[dict, PropertyAffordance]], List[Union[dict, PropertyAffordance]]]])

slots.thing__actions = Slot(uri=TD.actions, name="thing__actions", curie=TD.curie('actions'),
                   model_uri=TD.thing__actions, domain=None, range=Optional[Union[Dict[Union[str, ActionAffordanceName], Union[dict, ActionAffordance]], List[Union[dict, ActionAffordance]]]])

slots.thing__events = Slot(uri=TD.events, name="thing__events", curie=TD.curie('events'),
                   model_uri=TD.thing__events, domain=None, range=Optional[Union[Dict[Union[str, EventAffordanceName], Union[dict, EventAffordance]], List[Union[dict, EventAffordance]]]])