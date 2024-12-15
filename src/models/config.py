from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class Config(BaseModel):
    auth: str = Field("", description="Authentication token")
    seed: int = Field(0, ge=0, description="Problem seed (random if zero)")
    order_rate: int = Field(
        500,
        ge=1,
        description="The rate at which orders should be placed in milliseconds",
    )
    min_pickup: int = Field(4, ge=1, description="Minimum pickup time in seconds")
    max_pickup: int = Field(8, ge=1, description="Maximum pickup time in seconds")
    endpoint: str = Field("https://api.cloudkitchens.com", description="Problem server endpoint")
    problem_file_path: str = Field(
        None,
        description="Problem file path used for local testing outside docker environment.",
    )

    @model_validator(mode="after")
    def check_pickup_times(self) -> Self:
        if self.max_pickup < self.min_pickup:
            raise ValueError("max_pickup must be greater than or equal to min_pickup")
        return self

    @model_validator(mode="after")
    def check_problem_source(self) -> Self:
        if not self.problem_file_path and (not self.auth or not self.endpoint):
            raise ValueError("Problem source must be provided (auth and endpoint) or (problem_file_path)")
        return self
