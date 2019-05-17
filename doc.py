import mongoengine
class Doc(mongoengine.EmbeddedDocument):
    doc_id = mongoengine.ObjectIdField()
    meta_data = mongoengine.StringField()