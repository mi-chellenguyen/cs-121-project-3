import mongoengine
from doc import Doc

class IndexEntry(mongoengine.Document):
    # attributes of index object
    token = mongoengine.StringField(required=True)
    pages = mongoengine.EmbeddedDocumentListField(Doc)
    meta = {
        'db_alias': 'core',
        'collection': 'index'
        }