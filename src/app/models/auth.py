from sqlmodel import SQLModel, Field

class UserModel(SQLModel):
    username: str
    email: str

class UserAuthModel(UserModel, table=True):
    id: int = Field(default=None, primary_key=True)