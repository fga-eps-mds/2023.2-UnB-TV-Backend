import os
from  constants import errorMessages

def validate_dotenv():
  required_env_var = ["SECRET", "ALGORITHM", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_PORT", "MAIL_SERVER"]
  missing_env_var = [var for var in required_env_var if var not in os.environ]
  
  if missing_env_var:
    error_message = "{} (missing: {})".format(errorMessages.MISSING_ENV_VALUES, ', '.join(missing_env_var))
    raise EnvironmentError(error_message)