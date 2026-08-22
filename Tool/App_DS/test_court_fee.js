const fs = require('fs');
const path = require('path');
const vm = require('vm');


const html = fs.readFileSync(path.resolve(__dirname, 'index.html'), 'utf8');

if (!html.includes('⚠️ <strong>Khuyến cáo:</strong>') ||
    !html.includes('không thay thế cho các quyết định tố tụng chính thức')) {
    throw new Error('Missing professional-use advisory in the court-fee calculator.');
}

function extractFunction(name) {
    const start = html.indexOf(`function ${name}(`);
    if (start < 0) throw new Error(`Missing function: ${name}`);
    const brace = html.indexOf('{', start);
    let depth = 0;
    for (let index = brace; index < html.length; index += 1) {
        if (html[index] === '{') depth += 1;
        if (html[index] === '}') depth -= 1;
        if (depth === 0) return html.slice(start, index + 1);
    }
    throw new Error(`Unclosed function: ${name}`);
}

function calculate(type, value, discount = false) {
    const elements = {
        loai_phi: { value: type },
        gia_tri: { value: String(value) },
        giam_50: { checked: discount },
        receipt_gia_tri: { innerText: '' },
        receipt_cong_thuc: { innerText: '' },
        receipt_ket_qua_goc: { innerText: '' },
        receipt_ket_qua: { innerText: '' },
        receipt_so_giam: { innerText: '' },
        receipt_giam_row: { style: {} },
        receiptBlock: { style: {} },
    };
    const context = {
        document: { getElementById: id => elements[id] },
        alert: message => { throw new Error(message); },
    };
    vm.createContext(context);
    vm.runInContext(extractFunction('tinhAnPhi'), context);
    context.tinhAnPhi({ preventDefault() {} });
    return Number(elements.receipt_ket_qua.innerText.replaceAll('.', ''));
}

const cases = [
    ['ds_co_gia_ngach', 6_000_000, false, 300_000],
    ['ds_co_gia_ngach', 400_000_000, false, 20_000_000],
    ['ds_co_gia_ngach', 800_000_000, false, 36_000_000],
    ['ds_co_gia_ngach', 2_000_000_000, false, 72_000_000],
    ['ds_co_gia_ngach', 4_000_000_000, false, 112_000_000],
    ['ds_co_gia_ngach', 5_000_000_000, false, 113_000_000],
    ['kdtm_co_gia_ngach', 60_000_000, false, 3_000_000],
    ['kdtm_co_gia_ngach', 1_000_000, false, 3_000_000],
    ['kdtm_co_gia_ngach', 10_000_000, false, 3_000_000],
    ['kdtm_co_gia_ngach', 61_000_000, false, 3_050_000],
    ['kdtm_co_gia_ngach', 400_000_000, false, 20_000_000],
    ['lao_dong_co_gia_ngach', 6_000_000, false, 300_000],
    ['lao_dong_co_gia_ngach', 400_000_000, false, 12_000_000],
    ['lao_dong_co_gia_ngach', 2_000_000_000, false, 44_000_000],
    ['ds_co_gia_ngach', 800_000_000, true, 18_000_000],
];

for (const [type, value, discount, expected] of cases) {
    const actual = calculate(type, value, discount);
    if (actual !== expected) {
        throw new Error(`${type}/${value}/${discount}: expected ${expected}, received ${actual}`);
    }
}

console.log(`Court-fee cases passed: ${cases.length}`);
