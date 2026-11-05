from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal['ExerciseSession', 'Steps', 'Distance', 'ActiveCaloriesBurned', 'TotalCaloriesBurned',
                   'HeartRate', 'RestingHeartRate', 'SleepSession', 'Weight', 'Speed', 'ElevationGained']


class HealthRecord(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    category: Category
    id: str = Field(min_length=1, max_length=256)
    origin: str = Field(min_length=1, max_length=256)
    start: datetime
    end: datetime
    values: dict
    metadata: dict
    native: dict

    @model_validator(mode='after')
    def valid_time(self):
        if self.start.utcoffset() is None or self.end.utcoffset() is None or self.end < self.start:
            raise ValueError('Timezone-aware ordered timestamps required')
        return self


class ImportBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    installation_id: str = Field(min_length=1, max_length=128)
    records: list[HealthRecord] = Field(default_factory=list, max_length=200)
    deleted: list[str] = Field(default_factory=list, max_length=200)
