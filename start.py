import sys
sys.path.insert(0, '/app/localpress')
from app import app
print('  LocalPress running at http://localhost:5000')
app.run(host='0.0.0.0', port=5000, debug=False)
