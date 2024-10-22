import uvicorn
from dotenv import load_dotenv

load_dotenv()

from  utils import dotenv

load_dotenv()
dotenv.validate_dotenv()

if __name__ == '__main__': # pragma: no cover
  port = 8000
  uvicorn.run(' main:app', reload=True, port=int(port), host="0.0.0.0")