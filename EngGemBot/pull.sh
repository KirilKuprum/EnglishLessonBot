#!/bit/bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
system systemctl restart botGeminiAVS
echo "Successfully pulled botGeminiAVS!"