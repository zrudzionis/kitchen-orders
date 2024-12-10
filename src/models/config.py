from pydantic import BaseModel, Field, HttpUrl, model_validator


class Config(BaseModel):
    auth: str = Field(..., description="Authentication token")
    seed: int = Field(0, ge=0, description="Problem seed (random if zero)")
    order_rate: int = Field(
        500,
        ge=1,
        description="The rate at which orders should be placed in milliseconds",
    )
    min_pickup: int = Field(4, ge=1, description="Minimum pickup time in seconds")
    max_pickup: int = Field(8, ge=1, description="Maximum pickup time in seconds")
    endpoint: HttpUrl = Field(
        "https://api.cloudkitchens.com", description="Problem server endpoint"
    )

    @model_validator(mode="after")
    def check_pickup_times(self):
        if self.max_pickup < self.min_pickup:
            raise ValueError("max_pickup must be greater than or equal to min_pickup")
        return self
