with open('backend/api/router.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('route_clinical_case')
if idx != -1:
    print(text[idx-50:idx+600])
else:
    print("Not found")
