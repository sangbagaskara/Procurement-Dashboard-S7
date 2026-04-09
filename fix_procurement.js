#!/usr/bin/env node
/**
 * fix_procurement.js
 * Run: node fix_procurement.js
 * 
 * Fixes all GAS integration bugs in index.html
 * Output: index_fixed.html (ready to upload to GitHub)
 */

const fs = require('fs');
const path = require('path');

const inputFile = 'index.html';
const outputFile = 'index_fixed.html';

if (!fs.existsSync(inputFile)) {
    console.error(`ERROR: ${inputFile} not found in current directory`);
    console.error('Run this script from the same folder as index.html');
    process.exit(1);
}

let html = fs.readFileSync(inputFile, 'utf8');
console.log(`Input: ${(html.length/1024).toFixed(0)}KB`);

const changes = [];
function p(old, neu, name) {
    if (html.includes(old)) {
        html = html.split(old).join(neu);
        changes.push(`✓ ${name}`);
    } else {
        changes.push(`⚠ NOT FOUND: ${name}`);
    }
}

// ============================================================
// FIX 1: saveAllData — broken definition (called itself before declaration)
// ============================================================
p(
    `        saveAllData();                    // existing localStorage save\n` +
    `                saveToGAS(editedPackage);         // NEW: sync to Google Sheets {\n` +
    `            try {\n` +
    `                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n` +
    `                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n` +
    `                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n` +
    `                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n` +
    `                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n` +
    `                console.log('Data saved to localStorage successfully');\n` +
    `            } catch (e) {\n` +
    `                console.error('Error saving to localStorage:', e);\n` +
    `                showNotification('Error saving data. Storage may be full.', 'error');\n` +
    `            }\n` +
    `        }`,
    
    `        function saveAllData() {\n` +
    `            try {\n` +
    `                localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(projects));\n` +
    `                localStorage.setItem(STORAGE_KEYS.PACKAGES, JSON.stringify(packages));\n` +
    `                localStorage.setItem(STORAGE_KEYS.RISKS, JSON.stringify(risks));\n` +
    `                localStorage.setItem(STORAGE_KEYS.SELECTED_PROJECT, selectedProject.toString());\n` +
    `                localStorage.setItem(STORAGE_KEYS.WEIGHT_FACTORS, JSON.stringify(weightFactors));\n` +
    `            } catch (e) {\n` +
    `                console.error('Error saving to localStorage:', e);\n` +
    `                showNotification('Error saving data. Storage may be full.', 'error');\n` +
    `            }\n` +
    `        }`,
    'FIX 1: saveAllData definition'
);

// ============================================================
// FIX 2: fetchFromGAS — bad saveToGAS(editedPackage) calls inside
// ============================================================
p(
    `       \n` +
    `            saveAllData();                    // existing localStorage save\n` +
    `            saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n` +
    `        \n` +
    `        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');`,
    
    `       \n` +
    `        saveAllData();\n` +
    `        showNotification('Data synced from Google Sheets (' + packages.length + ' packages)', 'success');`,
    'FIX 2: fetchFromGAS bad calls'
);

// ============================================================
// FIX 3: fetchFromGAS — add response.ok check
// ============================================================
p(
    `        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n` +
    `        const data = await response.json();\n` +
    `        \n` +
    `        if (data.error) {`,
    
    `        const response = await fetch(GAS_CONFIG.URL + '?action=getAll');\n` +
    `        if (!response.ok) throw new Error('HTTP ' + response.status);\n` +
    `        const data = await response.json();\n` +
    `        \n` +
    `        if (data.error) {`,
    'FIX 3: fetchFromGAS response.ok check'
);

// ============================================================
// FIX 4: fetchFromGAS — fix catch block
// ============================================================
p(
    `    } catch(err) {\n` +
    `        console.error('GAS fetch failed:', err);\n` +
    `        showNotification('Offline mode \u2014 using cached data', 'warning');\n` +
    `        return false;\n` +
    `    }\n` +
    `}\n` +
    `\nasync function saveToGAS`,
    
    `    } catch(err) {\n` +
    `        console.warn('GAS fetch failed, using local cache:', err.message);\n` +
    `        showNotification('Offline \u2014 using cached data', 'warning');\n` +
    `        return false;\n` +
    `    }\n` +
    `}\n` +
    `\nasync function saveToGAS`,
    'FIX 4: fetchFromGAS catch block'
);

// ============================================================
// FIX 5: saveToGAS — full function replacement
// ============================================================
p(
    `async function saveToGAS(pkg) {\n` +
    `    if (!GAS_CONFIG.ENABLED) return;\n` +
    `    \n` +
    `    try {\n` +
    `        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n` +
    `        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n` +
    `        \n` +
    `        // Check URL length \u2014 GET limit ~2048 chars\n` +
    `        if (url.length > 8000) {\n` +
    `            console.warn('Payload too large for GET, saving to localStorage only');\n` +
    `            showNotification('Package saved locally (too large for sync)', 'warning');\n` +
    `            return;\n` +
    `        }\n` +
    `        \n` +
    `        const response = await fetch(url);\n` +
    `        const result = await response.json();\n` +
    `        \n` +
    `        if (result.success) {\n` +
    `            showNotification('Saved to Google Sheets', 'success');\n` +
    `            // Log activity\n` +
    `            logActivityToGAS('update', pkg.packageName, 'Package updated via dashboard');\n` +
    `        } else {\n` +
    `            showNotification('Save error: ' + (result.error || 'Unknown'), 'error');\n` +
    `        }\n` +
    `    } catch(err) {\n` +
    `        console.error('GAS save failed:', err);\n` +
    `        showNotification('Saved locally \u2014 will sync later', 'warning');\n` +
    `    }\n` +
    `}`,
    
    `async function saveToGAS(pkg) {\n` +
    `    if (!GAS_CONFIG.ENABLED || !pkg) return;\n` +
    `    \n` +
    `    try {\n` +
    `        const payload = btoa(unescape(encodeURIComponent(JSON.stringify(pkg))));\n` +
    `        const url = GAS_CONFIG.URL + '?action=updatePackage&data=' + payload;\n` +
    `        \n` +
    `        if (url.length > 8000) {\n` +
    `            console.warn('Payload too large for GET, skipping GAS sync');\n` +
    `            showNotification('Package saved locally (too large for sync)', 'warning');\n` +
    `            return;\n` +
    `        }\n` +
    `        \n` +
    `        const response = await fetch(url);\n` +
    `        if (!response.ok) throw new Error('HTTP ' + response.status);\n` +
    `        const result = await response.json();\n` +
    `        \n` +
    `        if (result.success) {\n` +
    `            showNotification('Saved to Google Sheets \u2713', 'success');\n` +
    `            logActivityToGAS('update', pkg.packageName || 'record', 'Updated via dashboard');\n` +
    `        } else {\n` +
    `            console.warn('GAS save warning:', result.error);\n` +
    `        }\n` +
    `    } catch(err) {\n` +
    `        console.warn('GAS save failed (offline?):', err.message);\n` +
    `    }\n` +
    `}`,
    'FIX 5: saveToGAS function'
);

// ============================================================
// FIX 6: initApp — render first, then async sync
// ============================================================
p(
    `async function initApp() {\n` +
    `    // Try loading from GAS first\n` +
    `    loadAllData(); // Load localStorage as fallback first\n` +
    `    \n` +
    `    if (GAS_CONFIG.ENABLED) {\n` +
    `        await fetchFromGAS();\n` +
    `    }\n` +
    `    \n` +
    `    renderAll();\n` +
    `    initCharts();\n` +
    `    initCutoffDate();\n` +
    `    switchTab('dashboard');\n` +
    `}`,
    
    `async function initApp() {\n` +
    `    loadAllData();\n` +
    `    populateSelects();\n` +
    `    renderAll();\n` +
    `    initCharts();\n` +
    `    initCutoffDate();\n` +
    `    switchTab('dashboard');\n` +
    `\n` +
    `    if (GAS_CONFIG.ENABLED) {\n` +
    `        const synced = await fetchFromGAS();\n` +
    `        if (synced) {\n` +
    `            populateSelects();\n` +
    `            renderAll();\n` +
    `            if (charts.discipline) updateCharts();\n` +
    `        }\n` +
    `    }\n` +
    `}`,
    'FIX 6: initApp'
);

// ============================================================
// FIX 7: changeProject — clean version
// ============================================================
p(
    `function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value);` +
    `                 saveAllData();                    // existing localStorage save\n` +
    `                saveToGAS(editedPackage);         // NEW: sync to Google Sheets; renderAll(); }`,
    
    `function changeProject() { selectedProject = parseInt(document.getElementById('projectSelect').value);` +
    ` saveAllData(); renderAll(); }`,
    'FIX 7: changeProject'
);

// ============================================================
// FIX 8: loadDataFromSupabase bad calls
// ============================================================
p(
    `                saveAllData();                    // existing localStorage save\n` +
    `                saveToGAS(editedPackage);         // NEW: sync to Google Sheets\n` +
    `                \n` +
    `                return true;`,
    
    `                saveAllData();\n` +
    `                \n` +
    `                return true;`,
    'FIX 8: loadDataFromSupabase'
);

// ============================================================
// FIX 9-N: Regex sweep for all remaining comment-paired patterns
// ============================================================
const badPattern = /saveAllData\(\);\s*\/\/[^\n]*localStorage[^\n]*\n\s*saveToGAS\(editedPackage\);[^\n]*\n/g;
const badMatches = html.match(badPattern) || [];
if (badMatches.length > 0) {
    html = html.replace(badPattern, 'saveAllData();\n');
    changes.push(`✓ FIX 9: Regex removed ${badMatches.length} comment-paired saveToGAS(editedPackage) calls`);
}

// ============================================================
// FIX 10: savePackage — add saveToGAS(pkg) after saveAllData
// ============================================================
p(
    `            saveAllData();\n` +
    `            showNotification(id?'Package updated successfully':'Package added successfully','success');\n` +
    `            closePackageModal();\n` +
    `            renderAll(); \n` +
    `        }`,
    
    `            saveAllData();\n` +
    `            saveToGAS(pkg);\n` +
    `            showNotification(id?'Package updated successfully':'Package added successfully','success');\n` +
    `            closePackageModal();\n` +
    `            renderAll(); \n` +
    `        }`,
    'FIX 10: savePackage -> saveToGAS(pkg)'
);

// ============================================================
// FINAL: brute-force remove any remaining saveToGAS(editedPackage)
// ============================================================
const remainingBefore = (html.match(/saveToGAS\(editedPackage\)/g) || []).length;
if (remainingBefore > 0) {
    html = html.replace(/[ \t]*saveToGAS\(editedPackage\);[^\n]*\n/g, '\n');
    const remainingAfter = (html.match(/saveToGAS\(editedPackage\)/g) || []).length;
    changes.push(`✓ FINAL: force-removed ${remainingBefore - remainingAfter} more saveToGAS(editedPackage) calls`);
}

// ============================================================
// WRITE OUTPUT
// ============================================================
fs.writeFileSync(outputFile, html, 'utf8');

const remaining = (html.match(/saveToGAS\(editedPackage\)/g) || []).length;

console.log('\nPatches applied:');
changes.forEach(c => console.log(`  ${c}`));
console.log(`\nOutput: ${(html.length/1024).toFixed(0)}KB → ${outputFile}`);
console.log(`Remaining bad calls: ${remaining}`);

if (remaining === 0) {
    console.log('\n✅ ALL FIXED — upload index_fixed.html to GitHub!');
} else {
    console.log(`\n⚠️  ${remaining} bad patterns remain — check manually`);
}
