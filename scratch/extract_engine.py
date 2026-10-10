# -*- coding: utf-8 -*-
from gen_engine import ENGINE_CODE
with open('scratch/test_engine.js', 'w', encoding='utf-8') as f:
    f.write(ENGINE_CODE)
print("Wrote scratch/test_engine.js, length:", len(ENGINE_CODE))
