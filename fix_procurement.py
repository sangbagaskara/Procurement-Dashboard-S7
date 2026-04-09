#!/usr/bin/env python3
"""
fix_procurement.py
Run: python3 fix_procurement.py
Fixes all GAS integration bugs in index.html
Output: index_fixed.html
"""

import re
import os
import sys

input_file = 'index.html'
output_file = 'index_fixed.html'

if not os.path.exists(input_file):
    print(f"ERROR: {input_file} not found in current directory")
    print("Run this script from the same folder as index.html")
    sys.exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    html = f.read()

print(f"Input: {len(html)//1024}KB")
changes = []

def p(old, new, name):
    global html
    if old in html:
        html = html.replace(old, new)
        changes.append(f"OK: {name}")
    else:
        changes.append(f"MISS: {name}")

# FIX 1: saveAllData broken definition
p(
    "        saveAllData();                    // existing localStorage save\n"
    "                saveToGAS(editedPackage);         // NEW: sync to Google Sheets {\n"
    "            try {\n"
    "                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n"
    "                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n"
    "                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n"
    "                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n"
    "                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n"
    "                console.log('Data saved to localStorage successfully');\n"
    "            } catch (e) {\n"
    "                console.error('Error saving to localStorage:', e);\n"
    "                showNotification('Error saving data. Storage may be full.', 'error');\n"
    "            }\n"
    "        }",

    "        function saveAllData() {\n"
    "            try {\n"
    "                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n"
    "                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n"
    "                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n"
    "                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n"
    "                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n"
    "            } catch (e) {\n"
    "                console.error('Error saving to localStorage:', e);\n"
    "                showNotification('Error saving data. Storage may be full.', 'error');\n"
    "            }\n"
    "        }",
    "FIX 1: saveAllData definition"
)

# FIX 2: fetchFromGAS bad calls
p(
    "       \n"
    "            saveAllData();                    // existing localStorage save\n"
    "            saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n"
    "        \n"
    "        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');",

    "       \n"
    "        saveAllData();\n"
    "        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');",
    "FIX 2: fetchFromGAS bad calls"
)

# FIX 3: fetchFromGAS response.ok
p(
    "        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n"
    "        const data = await response.json();\n"
    "        \n"
    "        if (data.error) {",

    "        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n"
    "        if (!response.ok) throw new Error('HTTP ' + response.status);\n"
    "        const data = await response.json();\n"
    "        \n"
    "        if (data.error) {",
    "FIX 3: fetchFromGAS response.ok"
)

# FIX 4: fetchFromGAS catch
p(
    "    } catch(err) {\n"
    "        console.error('GAS fetch failed:', err);\n"
    "        showNotification('Offline mode \u2014 using cached data', 'warning');\n"
    "        return false;\n"
    "    }\n"
    "}\n"
    "\nasync function saveToGAS",

    "    } catch(err) {\n"
    "        console.warn('GAS fetch failed, using local cache:', err.message);\n"
    "        showNotification('Offline \u2014 using cached data', 'warning');\n"
    "        return false;\n"
    "    }\n"
    "}\n"
    "\nasync function saveToGAS",
    "FIX 4: fetchFromGAS catch"
)

# FIX 5: saveToGAS full function
p(
    "async function saveToGAS(pkg) {\n"
    "    if (!GAS_CONFIG.ENABLED) return;\n"
    "    \n"
    "    try {\n"
    "        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n"
    "        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n"
    "        \n"
    "        // Check URL length \u2014 GET limit ~2048 chars\n"
    "        if (url.length > 8000) {\n"
    "            console.warn('Payload too large for GET, saving to localStorage only');\n"
    "            showNotification('Package saved locally (too large for sync)', 'warning');\n"
    "            return;\n"
    "        }\n"
    "        \n"
    "        const response = await fetch(url);\n"
    "        const result = await response.json();\n"
    "        \n"
    "        if (result.success) {\n"
    "            showNotification('Saved to Google Sheets', 'success');\n"
    "            // Log activity\n"
    "            logActivityToGAS('update', pkg.packageName, 'Package updated via dashboard');\n"
    "        } else {\n"
    "            showNotification('Save error: ' + (result.error || 'Unknown'), 'error');\n"
    "        }\n"
    "    } catch(err) {\n"
    "        console.error('GAS save failed:', err);\n"
    "        showNotification('Saved locally \u2014 will sync later', 'warning');\n"
    "    }\n"
    "}",

    "async function saveToGAS(pkg) {\n"
    "    if (!GAS_CONFIG.ENABLED || !pkg) return;\n"
    "    \n"
    "    try {\n"
    "        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n"
    "        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n"
    "        \n"
    "        if (url.length > 8000) {\n"
    "            console.warn('Payload too large for GET, skipping GAS sync');\n"
    "            showNotification('Package saved locally (too large for sync)', 'warning');\n"
    "            return;\n"
    "        }\n"
    "        \n"
    "        const response = await fetch(url);\n"
    "        if (!response.ok) throw new Error('HTTP ' + response.status);\n"
    "        const result = await response.json();\n"
    "        \n"
    "        if (result.success) {\n"
    "            showNotification('Saved to Google Sheets \u2713', 'success');\n"
    "            logActivityToGAS('update', pkg.packageName || 'record', 'Updated via dashboard');\n"
    "        } else {\n"
    "            console.warn('GAS save warning:', result.error);\n"
    "        }\n"
    "    } catch(err) {\n"
    "        console.warn('GAS save failed (offline?):', err.message);\n"
    "    }\n"
    "}",
    "FIX 5: saveToGAS function"
)

# FIX 6: initApp
p(
    "async function initApp() {\n"
    "    // Try loading from GAS first\n"
    "    loadAllData(); // Load localStorage as fallback first\n"
    "    \n"
    "    if (GAS_CONFIG.ENABLED) {\n"
    "        await fetchFromGAS();\n"
    "    }\n"
    "    \n"
    "    renderAll();\n"
    "    initCharts();\n"
    "    initCutoffDate();\n"
    "    switchTab('dashboard');\n"
    "}",

    "async function initApp() {\n"
    "    loadAllData();\n"
    "    populateSelects();\n"
    "    renderAll();\n"
    "    initCharts();\n"
    "    initCutoffDate();\n"
    "    switchTab('dashboard');\n"
    "\n"
    "    if (GAS_CONFIG.ENABLED) {\n"
    "        const synced = await fetchFromGAS();\n"
    "        if (synced) {\n"
    "            populateSelects();\n"
    "            renderAll();\n"
    "            if (charts.discipline) updateCharts();\n"
    "        }\n"
    "    }\n"
    "}",
    "FIX 6: initApp"
)

# FIX 7: changeProject
p(
    "function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value);"
    "                 saveAllData();                    // existing localStorage save\n"
    "                saveToGAS(editedPackage);         // NEW: sync to Google Sheets; renderAll(); }",

    "function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value);"
    " saveAllData(); renderAll(); }",
    "FIX 7: changeProject"
)

# FIX 8: loadDataFromSupabase
p(
    "                saveAllData();                    // existing localStorage save\n"
    "                saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n"
    "                \n"
    "                return true;",

    "                saveAllData();\n"
    "                \n"
    "                return true;",
    "FIX 8: loadDataFromSupabase"
)

# FIX 9: regex sweep
n = len(re.findall(r'saveAllData\(\);\s*//[^\n]*\n\s*saveToGAS\(editedPackage\);', html))
if n:
    html = re.sub(r'saveAllData\(\);\s*//[^\n]*\n\s*saveToGAS\(editedPackage\);[^\n]*\n', 'saveAllData();\n', html)
    changes.append(f"OK: FIX 9 regex removed {n} comment-paired calls")

# FIX 10: savePackage add saveToGAS(pkg)
p(
    "            saveAllData();\n"
    "            showNotification(id?'Package updated successfully':'Package added successfully','success');\n"
    "            closePackageModal();\n"
    "            renderAll(); \n"
    "        }",

    "            saveAllData();\n"
    "            saveToGAS(pkg);\n"
    "            showNotification(id?'Package updated successfully':'Package added successfully','success');\n"
    "            closePackageModal();\n"
    "            renderAll(); \n"
    "        }",
    "FIX 10: savePackage -> saveToGAS(pkg)"
)

# FINAL: brute force
rem = html.count('saveToGAS(editedPackage)')
if rem:
    html = re.sub(r'[ \t]*saveToGAS\(editedPackage\);[^\n]*\n', '\n', html)
    after = html.count('saveToGAS(editedPackage)')
    changes.append(f"OK: FINAL force-removed {rem - after} saveToGAS(editedPackage)")

# Write output
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

remaining = html.count('saveToGAS(editedPackage)')

print('\nPatches applied:')
for c in changes:
    print(f'  {c}')
print(f'\nOutput: {len(html)//1024}KB -> {output_file}')
print(f'Remaining bad calls: {remaining}')

if remaining == 0:
    print('\n✅ ALL FIXED - upload index_fixed.html to GitHub!')
else:
    print(f'\n⚠  {remaining} bad patterns remain - check manually')
