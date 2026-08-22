const fs = require('fs');
const path = require('path');
const vm = require('vm');


const htmlPath = path.resolve(__dirname, '..', 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

for (const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    new vm.Script(match[1]);
}

for (const marker of [
    'Cơ sở tính lãi theo thỏa thuận:',
    'id="co_so_tinh_lai"',
    'value="du_no_thuc_te"',
    'value="goc_ban_dau_co_dinh"',
    'Chỉ chọn nợ gốc ban đầu cố định khi hợp đồng hoặc chứng từ ghi rõ',
]) {
    if (!html.includes(marker)) throw new Error(`Missing interest-basis UI marker: ${marker}`);
}
if (html.includes('id="phuong_thuc"') || html.includes('Phương thức trả lãi:')) {
    throw new Error('The obsolete repayment-method selector is still visible in the UI.');
}

function extractFunction(name) {
    const marker = `function ${name}(`;
    const start = html.indexOf(marker);
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

const functionNames = [
    'parseDate', 'addDays', 'daysBetween', 'formatDateStr',
    'getDaysPerYear', 'decomposeTotalDays', 'decomposePeriod',
    'calcInterestPeriod', 'formatDecomposeText', 'mergeDetail',
    'tinhToanChiTiet',
];
const context = {};
vm.createContext(context);
vm.runInContext(functionNames.map(extractFunction).join('\n'), context);

function assertEqual(actual, expected, label) {
    if (actual !== expected) {
        throw new Error(`${label}: expected ${expected}, received ${actual}`);
    }
}

function roundedInterest(principal, rate, start, end) {
    return Math.round(context.calcInterestPeriod(
        principal, rate, new Date(`${start}T00:00:00`), new Date(`${end}T00:00:00`)
    ).totalInterest);
}

assertEqual(
    roundedInterest(100_000_000, 10.8, '2017-12-20', '2017-12-30'),
    300_000,
    '360-day basis before 2018',
);
assertEqual(
    roundedInterest(100_000_000, 10.8, '2018-01-01', '2018-01-11'),
    295_890,
    '365-day basis from 2018',
);
assertEqual(
    roundedInterest(100_000_000, 10.8, '2017-12-30', '2018-01-03'),
    119_178,
    'period crossing 01/01/2018',
);

const statementRows = [
    ['2025-10-10', '2025-11-15', 1_074_000_000, 10.8, 11_440_307],
    ['2025-11-15', '2025-12-15', 1_052_941_000, 10.8, 9_346_654],
    ['2025-12-15', '2025-12-22', 1_052_941_000, 10.8, 2_180_886],
    ['2025-12-22', '2026-01-15', 1_031_882_000, 10.8, 7_327_776],
    ['2026-01-15', '2026-02-23', 1_010_823_000, 10.8, 11_664_620],
    ['2026-02-23', '2026-02-27', 1_010_823_000, 10.8, 1_196_371],
    ['2026-02-27', '2026-03-16', 1_010_822_000, 10.8, 5_084_573],
    ['2026-03-16', '2026-04-15', 1_010_822_000, 10.8, 8_972_776],
    ['2026-04-15', '2026-05-07', 1_010_822_000, 10.8, 6_580_036],
    ['2026-05-07', '2026-05-15', 947_646_000, 10.8, 2_243_195],
    ['2026-05-15', '2026-08-11', 947_646_000, 16.2, 37_012_716],
];
for (const [start, end, principal, rate, expectedInterest] of statementRows) {
    assertEqual(
        roundedInterest(principal, rate, start, end),
        expectedInterest,
        `bank statement row ${start}..${end}`,
    );
}

const result = context.tinhToanChiTiet({
    so_tien_vay: 1_074_000_000,
    lai_suat_nam: 10.8,
    loai_lai_suat: 'nam',
    lai_suat_thoa_thuan_qh: '',
    loai_lai_suat_qh: 'nam',
    phuong_thuc: 'du_no_giam_dan',
    thoi_han_nam: 0,
    thoi_han_thang: 7,
    thoi_han_ngay: 5,
    ngay_vay: '2025-10-10',
    ngay_tra_thuc_te: '2026-08-10',
    list_tha_noi: [],
    list_thanh_toan: [
        { date: '2025-11-15', goc: 21_059_000, lai: 11_440_307 },
        { date: '2025-12-15', goc: 0, lai: 395_166 },
        { date: '2025-12-22', goc: 21_059_000, lai: 9_034_082 },
        { date: '2026-01-15', goc: 21_059_000, lai: 9_465_044 },
        { date: '2026-02-23', goc: 0, lai: 3_767 },
        { date: '2026-02-27', goc: 1_000, lai: 0 },
        { date: '2026-05-07', goc: 63_176_000, lai: 28_156_469 },
    ],
});

const actual = {
    principalRemaining: Math.round(result.matrix.goc.tong),
    inTermInterestRemaining: Math.round(result.matrix.lth.tong),
    overdueInterest: Math.round(result.matrix.lqh.tong),
    lateInterest: Math.round(result.matrix.lct.tong),
    totalRemaining: Math.round(result.matrix.tong.tong),
};
const expected = {
    principalRemaining: 947_646_000,
    inTermInterestRemaining: 7_542_360,
    overdueInterest: 37_012_716,
    lateInterest: 0,
    totalRemaining: 992_201_076,
};

console.log(JSON.stringify({ actual, expected }, null, 2));
if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    console.log(result.dien_giai);
    process.exit(1);
}

const basisPayload = {
    so_tien_vay: 100_000_000,
    lai_suat_nam: 10,
    loai_lai_suat: 'nam',
    lai_suat_thoa_thuan_qh: '',
    loai_lai_suat_qh: 'nam',
    lai_suat_cham_tra: 0,
    thoi_han_nam: 1,
    thoi_han_thang: 0,
    thoi_han_ngay: 0,
    ngay_vay: '2025-01-01',
    ngay_tra_thuc_te: '2025-01-10',
    list_tha_noi: [],
    list_thanh_toan: [{ date: '2025-01-06', goc: 50_000_000, lai: 0 }],
};
const actualBalanceBasis = context.tinhToanChiTiet({
    ...basisPayload,
    co_so_tinh_lai: 'du_no_thuc_te',
});
const fixedInitialBasis = context.tinhToanChiTiet({
    ...basisPayload,
    co_so_tinh_lai: 'goc_ban_dau_co_dinh',
});
assertEqual(
    Math.round(actualBalanceBasis.matrix.lth.tong),
    205_479,
    'actual outstanding balance after partial principal payment',
);
assertEqual(
    Math.round(fixedInitialBasis.matrix.lth.tong),
    273_973,
    'fixed initial principal when explicitly selected',
);

const floatingPayload = {
    ...basisPayload,
    list_thanh_toan: [],
    co_so_tinh_lai: 'du_no_thuc_te',
    list_tha_noi: [{ rate: 20, unit: 'nam', from: '2025-01-06', to: '2025-01-10' }],
};
const floatingResult = context.tinhToanChiTiet(floatingPayload);
assertEqual(
    Math.round(floatingResult.matrix.lth.tong),
    410_959,
    'floating annual rate replaces the base rate for its inclusive date range',
);

const monthlyFloatingResult = context.tinhToanChiTiet({
    ...basisPayload,
    list_thanh_toan: [],
    co_so_tinh_lai: 'du_no_thuc_te',
    list_tha_noi: [{ rate: 1.5, unit: 'thang', from: '2025-01-01', to: '2025-01-10' }],
});
assertEqual(
    Math.round(monthlyFloatingResult.matrix.lth.tong),
    493_151,
    'monthly floating rate is converted to an annual rate',
);

const floatingAfterRepayment = context.tinhToanChiTiet({
    ...floatingPayload,
    list_thanh_toan: [{ date: '2025-01-06', goc: 50_000_000, lai: 0 }],
});
assertEqual(
    Math.round(floatingAfterRepayment.matrix.lth.tong),
    273_973,
    'floating rate uses the reduced balance after a principal payment',
);

const multipleFloatingPeriods = context.tinhToanChiTiet({
    ...basisPayload,
    list_thanh_toan: [],
    co_so_tinh_lai: 'du_no_thuc_te',
    list_tha_noi: [
        { rate: 8, unit: 'nam', from: '2025-01-01', to: '2025-01-03' },
        { rate: 12, unit: 'nam', from: '2025-01-04', to: '2025-01-06' },
        { rate: 15, unit: 'nam', from: '2025-01-07', to: '2025-01-10' },
    ],
});
assertEqual(
    Math.round(multipleFloatingPeriods.matrix.lth.tong),
    328_767,
    'multiple consecutive floating-rate periods are all applied',
);
