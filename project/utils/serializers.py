from rest_framework.serializers import (
    SerializerMetaclass,
    SerializerMethodField,
)


class SuccessMessageMixin(metaclass=SerializerMetaclass):
    """
    Provides a static yet customizable detail field to all inheriting
    serializers to be used as success message.
    """
    detail = SerializerMethodField()

    def get_detail(self, obj):
        raise NotImplementedError(
            "Please implement get_detail when using SuccessMessageMixin"
        )
