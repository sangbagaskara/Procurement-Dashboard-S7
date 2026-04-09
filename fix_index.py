#!/usr/bin/env python3
import sys, re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f"Input: {len(html):,} chars")
changes = []

def p(old, new, name):
    global html
    if old in html:
        html = html.replace(old, new)
        changes.append(f"✓ {name}")
    else:
        changes.append(f"⚠ MISS: {name}")

# FIX 1: saveAllData broken definition
p(
    "        saveAllData();                    // existing localStorage save\n                saveToGAS(editedPackage);         // NEW: sync to Google Sheets {\n            try {\n                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n                console.log('Data saved to localStorage successfully');\n            } catch (e) {\n                console.error('Error saving to localStorage:', e);\n                showNotification('Error saving data. Storage may be full.', 'error');\n            }\n        }",
    "        function saveAllData() {\n            try {\n                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n            } catch (e) {\n                console.error('Error saving to localStorage:', e);\n                showNotification('Error saving data. Storage may be full.', 'error');\n            }\n        }",
    "saveAllData definition"
)

# FIX 2: fetchFromGAS bad calls inside
p(
    "       \n            saveAllData();                    // existing localStorage save\n            saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n        \n        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');",
    "       \n        saveAllData();\n        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');",
    "fetchFromGAS bad calls"
)

# FIX 3: fetchFromGAS add response.ok check
p(
    "        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n        const data = await response.json();\n        \n        if (data.error) {",
    "        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n        if (!response.ok) throw new Error('HTTP ' + response.status);\n        const data = await response.json();\n        \n        if (data.error) {",
    "fetchFromGAS response.ok check"
)

# FIX 4: fetchFromGAS catch block
p(
    "    } catch(err) {\n        console.error('GAS fetch failed:', err);\n        showNotification('Offline mode — using cached data', 'warning');\n        return false;\n    }\n}\n\nasync function saveToGAS",
    "    } catch(err) {\n        console.warn('GAS fetch failed, using local cache:', err.message);\n        showNotification('Offline — using cached data', 'warning');\n        return false;\n    }\n}\n\nasync function saveToGAS",
    "fetchFromGAS catch block"
)

# FIX 5: saveToGAS full function
p(
    "async function saveToGAS(pkg) {\n    if (!GAS_CONFIG.ENABLED) return;\n    \n    try {\n        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n        \n        // Check URL length — GET limit ~2048 chars\n        if (url.length > 8000) {\n            console.warn('Payload too large for GET, saving to localStorage only');\n            showNotification('Package saved locally (too large for sync)', 'warning');\n            return;\n        }\n        \n        const response = await fetch(url);\n        const result = await response.json();\n        \n        if (result.success) {\n            showNotification('Saved to Google Sheets', 'success');\n            // Log activity\n            logActivityToGAS('update', pkg.packageName, 'Package updated via dashboard');\n        } else {\n            showNotification('Save error: ' + (result.error || 'Unknown'), 'error');\n        }\n    } catch(err) {\n        console.error('GAS save failed:', err);\n        showNotification('Saved locally — will sync later', 'warning');\n    }\n}",
    "async function saveToGAS(pkg) {\n    if (!GAS_CONFIG.ENABLED || !pkg) return;\n    \n    try {\n        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n        \n        if (url.length > 8000) {\n            console.warn('Payload too large for GET, skipping GAS sync');\n            showNotification('Package saved locally (too large for sync)', 'warning');\n            return;\n        }\n        \n        const response = await fetch(url);\n        if (!response.ok) throw new Error('HTTP ' + response.status);\n        const result = await response.json();\n        \n        if (result.success) {\n            showNotification('Saved to Google Sheets ✓', 'success');\n            logActivityToGAS('update', pkg.packageName || 'record', 'Updated via dashboard');\n        } else {\n            console.warn('GAS save warning:', result.error);\n        }\n    } catch(err) {\n        console.warn('GAS save failed (offline?):', err.message);\n    }\n}",
    "saveToGAS function"
)

# FIX 6: initApp function
p(
    "async function initApp() {\n    // Try loading from GAS first\n    loadAllData(); // Load localStorage as fallback first\n    \n    if (GAS_CONFIG.ENABLED) {\n        await fetchFromGAS();\n    }\n    \n    renderAll();\n    initCharts();\n    initCutoffDate();\n    switchTab('dashboard');\n}",
    "async function initApp() {\n    loadAllData();\n    populateSelects();\n    renderAll();\n    initCharts();\n    initCutoffDate();\n    switchTab('dashboard');\n\n    if (GAS_CONFIG.ENABLED) {\n        const synced = await fetchFromGAS();\n        if (synced) {\n            populateSelects();\n            renderAll();\n            if (charts.discipline) updateCharts();\n        }\n    }\n}",
    "initApp function"
)

# FIX 7: changeProject
p(
    "function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value);                 saveAllData();                    // existing localStorage save\n                saveToGAS(editedPackage);         // NEW: sync to Google Sheets; renderAll(); }",
    "function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value); saveAllData(); renderAll(); }",
    "changeProject function"
)

# FIX 8: loadDataFromSupabase bad calls
p(
    "                saveAllData();                    // existing localStorage save\n                saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n                \n                return true;",
    "                saveAllData();\n                \n                return true;",
    "loadDataFromSupabase"
)

# FIX 9: Regex sweep - remaining comment-paired calls
count = len(re.findall(r'saveAllData\(\);\s*//[^\n]*localStorage[^\n]*\n\s*saveToGAS\(editedPackage\);', html))
if count:
    html = re.sub(r'saveAllData\(\);\s*//[^\n]*localStorage[^\n]*\n\s*saveToGAS\(editedPackage\);[^\n]*\n', 'saveAllData();\n', html)
    changes.append(f"✓ Regex removed {count} comment-paired calls")

# FIX 10: savePackage - add saveToGAS(pkg)
p(
    "            saveAllData();\n            showNotification(id?'Package updated successfully':'Package added successfully','success');\n            closePackageModal();\n            renderAll(); \n        }",
    "            saveAllData();\n            saveToGAS(pkg);\n            showNotification(id?'Package updated successfully':'Package added successfully','success');\n            closePackageModal();\n            renderAll(); \n        }",
    "savePackage adds saveToGAS(pkg)"
)

# FINAL: force-remove any remaining
remaining = html.count('saveToGAS(editedPackage)')
if remaining > 0:
    html = re.sub(r'[ \t]*saveToGAS\(editedPackage\);[^\n]*\n', '\n', html)
    changes.append(f"✓ Force-removed {remaining} remaining saveToGAS(editedPackage)")

# Write output
with open('index_fixed.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Output: {len(html):,} chars → index_fixed.html")
print("\nPatches:")
for c in changes: print(f"  {c}")
print(f"\nRemaining bad calls: {html.count('saveToGAS(editedPackage)')}")
