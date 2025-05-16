from gitbase import GitBase, PlayerDataSystem, DataSystem, KeyValue, NotificationManager
from cryptography.fernet import Fernet

# Initialize GitHub database and encryption key
GITHUB_TOKEN = "YOUR-GITHUB-TOKEN"
REPO_OWNER = "YOUR-GITHUB-USERNAME"
REPO_NAME = "YOUR-GITHUB-REPO-NAME"
encryption_key = Fernet.generate_key()

# Setup GitBase with GitHub credentials
database = GitBase(GITHUB_TOKEN, REPO_OWNER, REPO_NAME)
player_data_system = PlayerDataSystem(db=database, encryption_key=encryption_key)
data_system = DataSystem(db=database, encryption_key=encryption_key)

cipher_suite = Fernet(key=encryption_key)