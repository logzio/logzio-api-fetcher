from enum import Enum
import logging
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class StopCondition(Enum):
    """
    Supported Stop conditions
    """
    EMPTY = "empty"
    EQUALS = "equals"
    CONTAINS = "contains"


class StopPaginationSettings(BaseModel):
    """
    Class that initialize API pagination settings stop condition.
    :param field: the field in the response to check the stop condition on
    :param condition: the condition to check on the field
    :param value: the stop value of the field to check, required only if condition is 'equals' or 'contains'
    """
    field: str
    condition: StopCondition
    value: str = Field(default=None, frozen=True)

    @model_validator(mode='after')
    def _check_conditional_fields(self):
        """
        Validates that:
        if we got condition as 'contains' or 'equals' >> that we also got value
        :return: self
        """
        if self.condition in (StopCondition.EQUALS, StopCondition.CONTAINS) and not self.value:
            raise ValueError(f"Used stop condition {self.condition} but missing required 'value' field.")
        return self

    def should_stop(self, field_value):
        """
        Returns True if the stop condition is met, False otherwise.
        :param field_value: they value of 'self.field' in the response (None if it doesn't exist)
        :return: True if the stop condition is met, False otherwise
        """
        if self.condition == StopCondition.EMPTY:
            return not field_value
        elif self.condition == StopCondition.EQUALS:
            return self.value == field_value
        elif self.condition == StopCondition.CONTAINS:
            return self.value in field_value
        else:
            logger.warning("Warning: Got invalid stop condition", self.condition)
        return True
