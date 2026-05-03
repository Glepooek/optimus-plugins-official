import { test } from '@playwright/test';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const testConfig = {
  outputDir: './test-results',
  reportDir: './test-report',
  screenshotDir: './test-screenshots',
  midsceneReportDir: './midscene_run/report',
  storageStatePath: './e2e/.auth/state.json',
  testScripts: [
    'e2e/oral-practice-entry.spec.ts',
  ],
};

function ensureDir(dirPath: string) {
  if (!fs.existsSync(dirPath)) fs.mkdirSync(dirPath, { recursive: true });
}

function prepareAuthState(): void {
  console.log('=== prepareAuthState ===');
  ensureDir(path.dirname(testConfig.storageStatePath));
  const absPath = path.resolve(testConfig.storageStatePath);
  if (fs.existsSync(absPath)) {
    const data = fs.readFileSync(absPath, 'utf-8');
    const parsed = JSON.parse(data);
    const cookieCount = parsed.cookies?.length || 0;
    const originCount = parsed.origins?.length || 0;
    console.log('state.json found | cookies: ' + cookieCount + ', origins: ' + originCount);
    if (cookieCount === 0 && originCount === 0) {
      console.warn('WARNING: state.json is empty, tests may run without login');
    }
  } else {
    console.warn('WARNING: state.json not found, tests will run without login');
    console.warn('Run auth.setup.ts first: npx playwright test e2e/auth.setup.ts --project=setup --headed');
  }
}

function createTempConfig(): string {
  const storageState = path.resolve(testConfig.storageStatePath).replace(/\\/g, '/');
  const outputDir = path.resolve(testConfig.outputDir).replace(/\\/g, '/');

  const configContent = `import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
import path from "path";
dotenv.config({ path: path.resolve("${process.cwd().replace(/\\/g, '/')}", ".env") });
export default defineConfig({
  testDir: "./e2e",
  testMatch: ["**/*.spec.ts"],
  timeout: 10 * 60 * 1000,
  fullyParallel: false,
  retries: 0,
  workers: 1,
  outputDir: "${outputDir}",
  reporter: [
    ["line"],
    ["json"],
    ["@midscene/web/playwright-report"]
  ],
  use: {
    trace: "on",
    screenshot: "on",
    video: "on",
  },

  projects: [{
    name: "chromium",
    use: {
      ...devices["Desktop Chrome"],
      viewport: { width: 1536, height: 864 },
      storageState: "${storageState}",
      permissions: ["microphone"],
      launchOptions: {
        args: [
          "--use-fake-ui-for-media-stream",
          "--use-fake-device-for-media-stream",
          "--allow-file-access"
        ]
      }
    }
  }],
});
`;
  const tempPath = path.resolve('playwright-temp.config.ts');
  fs.writeFileSync(tempPath, configContent, 'utf-8');
  return tempPath;
}

function runScript(script: string, jsonOutputPath: string, configPath: string): Promise<{ exitCode: number; stderr: string }> {
  return new Promise((resolve) => {
    const args = ['playwright', 'test', script, '--config=' + configPath, '--headed'];
    const cwd = process.cwd();
    const child = spawn('npx', args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
      cwd: cwd,
      timeout: 15 * 60 * 1000,
      env: {
        ...process.env,
        PLAYWRIGHT_JSON_OUTPUT_NAME: jsonOutputPath,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
        OPENAI_BASE_URL: process.env.OPENAI_BASE_URL || '',
        MIDSCENE_MODEL_NAME: process.env.MIDSCENE_MODEL_NAME || '',
        MIDSCENE_USE_QWEN_VL: process.env.MIDSCENE_USE_QWEN_VL || '',
        MIDSCENE_USE_DOUBAO_VISION: process.env.MIDSCENE_USE_DOUBAO_VISION || '',
      },
    });
    let stderr = '';
    child.stdout.on('data', (data: Buffer) => {
      const text = data.toString();
      const lines = text.split('\n').filter((l: string) => l.trim());
      for (const line of lines) console.log('  [' + path.basename(script) + '] ' + line);
    });
    child.stderr.on('data', (data: Buffer) => {
      const text = data.toString();
      stderr += text;
      if (!text.includes('ExperimentalWarning')) console.log('  [' + path.basename(script) + ' stderr] ' + text.trim());
    });
    child.on('close', (code: number | null) => resolve({ exitCode: code ?? 1, stderr }));
    child.on('error', (err: Error) => {
      console.error('  spawn error: ' + err.message);
      resolve({ exitCode: 1, stderr: err.message });
    });
  });
}

interface TestResult { testName: string; status: string; duration: number; error?: string; scriptName: string; timestamp: string; }

class TestResultCollector {
  results: TestResult[] = [];
  add(testName: string, status: string, duration: number, scriptName: string, error?: string) {
    this.results.push({ testName, status, duration, scriptName, error, timestamp: new Date().toISOString() });
  }
  get summary() {
    const total = this.results.length;
    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    return { total, passed, failed, passRate: total > 0 ? ((passed / total) * 100).toFixed(1) + '%' : '0%' };
  }
}

function extractResults(jsonPath: string, scriptName: string, collector: TestResultCollector) {
  if (!fs.existsSync(jsonPath)) { console.log('JSON not found: ' + jsonPath); return; }
  try {
    const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
    function walkSuites(suites: any[]) {
      for (const suite of suites) {
        for (const spec of (suite.specs || [])) {
          for (const t of (spec.tests || [])) {
            const r = (t.results || [])[t.results.length - 1];
            collector.add(spec.title || 'unknown', r?.status || 'unknown', r?.duration || 0, scriptName, r?.error?.message);
          }
        }
        if (suite.suites) walkSuites(suite.suites);
      }
    }
    walkSuites(data.suites || []);
    console.log('Extracted ' + collector.results.filter(r => r.scriptName === scriptName).length + ' results');
  } catch (e: any) { console.error('Parse error: ' + e.message); }
}

function generateTestReport(collector: TestResultCollector) {
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const s = collector.summary;
  const jsonPath = path.join(testConfig.reportDir, 'test-report-' + ts + '.json');
  fs.writeFileSync(jsonPath, JSON.stringify({ timestamp: new Date().toISOString(), summary: s, results: collector.results }, null, 2));
  console.log('JSON report: ' + jsonPath);

  const rows = collector.results.map(r => {
    const icon = r.status === 'passed' ? '✅' : r.status === 'failed' ? '❌' : '⏭️';
    const statusClass = r.status === 'passed' ? 'pass' : r.status === 'failed' ? 'fail' : 'skip';
    const err = r.error ? '<pre>' + r.error.substring(0, 300) + '</pre>' : '-';
    return '<tr class="' + statusClass + '"><td>' + icon + ' ' + r.status.toUpperCase() + '</td><td>' + r.scriptName + '</td><td>' + r.testName + '</td><td>' + (r.duration / 1000).toFixed(1) + 's</td><td>' + err + '</td></tr>';
  }).join('\n');

  const durations = collector.results.map(r => (r.duration / 1000).toFixed(1));
  const labels = collector.results.map(r => r.testName.length > 30 ? r.testName.substring(0, 30) + '...' : r.testName);
  const bgColors = collector.results.map(r => r.status === 'passed' ? '#4caf50' : r.status === 'failed' ? '#f44336' : '#ff9800');
  const skipped = s.total - s.passed - s.failed;

  const html = '<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="utf-8"><title>Test Report - ' + ts + '</title>\n'
    + '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\/script>\n'
    + '<style>\n'
    + '*{box-sizing:border-box;margin:0;padding:0}\n'
    + 'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;padding:20px}\n'
    + '.container{max-width:1200px;margin:0 auto}\n'
    + 'h1{font-size:24px;margin-bottom:8px;color:#1a1a1a}\n'
    + '.timestamp{color:#666;font-size:13px;margin-bottom:20px}\n'
    + '.summary-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}\n'
    + '.card{background:#fff;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)}\n'
    + '.card .num{font-size:36px;font-weight:700;margin-bottom:4px}\n'
    + '.card .label{font-size:13px;color:#888}\n'
    + '.card.total .num{color:#1890ff}.card.pass .num{color:#52c41a}.card.fail .num{color:#ff4d4f}.card.rate .num{color:#722ed1}\n'
    + '.charts{display:grid;grid-template-columns:1fr 2fr;gap:16px;margin-bottom:24px}\n'
    + '.chart-box{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}\n'
    + '.chart-box h3{font-size:15px;margin-bottom:12px;color:#555}\n'
    + 'table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)}\n'
    + 'th{background:#fafafa;padding:12px 16px;text-align:left;font-weight:600;font-size:13px;color:#666;border-bottom:2px solid #f0f0f0}\n'
    + 'td{padding:12px 16px;border-bottom:1px solid #f5f5f5;font-size:13px}\n'
    + 'tr.pass td:first-child{color:#52c41a}tr.fail td:first-child{color:#ff4d4f;font-weight:600}tr.skip td:first-child{color:#faad14}\n'
    + 'pre{white-space:pre-wrap;max-width:400px;font-size:12px;color:#cf1322;background:#fff2f0;padding:8px;border-radius:4px}\n'
    + '</style></head>\n<body><div class="container">\n'
    + '<h1>📊 E2E Test Report</h1>\n'
    + '<p class="timestamp">Generated: ' + new Date().toLocaleString('zh-CN') + '</p>\n'
    + '<div class="summary-cards">\n'
    + '<div class="card total"><div class="num">' + s.total + '</div><div class="label">Total</div></div>\n'
    + '<div class="card pass"><div class="num">' + s.passed + '</div><div class="label">Passed</div></div>\n'
    + '<div class="card fail"><div class="num">' + s.failed + '</div><div class="label">Failed</div></div>\n'
    + '<div class="card rate"><div class="num">' + s.passRate + '</div><div class="label">Pass Rate</div></div>\n'
    + '</div>\n'
    + '<div class="charts">\n'
    + '<div class="chart-box"><h3>Pass / Fail Distribution</h3><canvas id="pieChart"></canvas></div>\n'
    + '<div class="chart-box"><h3>Test Duration (seconds)</h3><canvas id="barChart"></canvas></div>\n'
    + '</div>\n'
    + '<table><thead><tr><th>Status</th><th>Script</th><th>Test Case</th><th>Duration</th><th>Error</th></tr></thead>\n'
    + '<tbody>' + rows + '</tbody></table>\n'
    + '</div>\n<script>\n'
    + 'new Chart(document.getElementById("pieChart"),{type:"doughnut",data:{labels:["Passed","Failed","Skipped"],datasets:[{data:[' + s.passed + ',' + s.failed + ',' + skipped + '],backgroundColor:["#52c41a","#ff4d4f","#faad14"],borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,plugins:{legend:{position:"bottom"}}}});\n'
    + 'new Chart(document.getElementById("barChart"),{type:"bar",data:{labels:' + JSON.stringify(labels) + ',datasets:[{label:"Duration (s)",data:[' + durations.join(',') + '],backgroundColor:' + JSON.stringify(bgColors) + ',borderRadius:6,borderSkipped:false}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,title:{display:true,text:"Seconds"}},x:{ticks:{maxRotation:45}}}}});\n'
    + '<\/script></body></html>';

  const htmlPath = path.join(testConfig.reportDir, 'test-report-' + ts + '.html');
  fs.writeFileSync(htmlPath, html);
  console.log('HTML report: ' + htmlPath);
}

test.describe('Complete Test Suite', () => {
  test.beforeAll(async () => {
    console.log('=== Init ===');
    ensureDir(testConfig.outputDir);
    ensureDir(testConfig.reportDir);
    ensureDir(testConfig.screenshotDir);
    ensureDir(testConfig.midsceneReportDir);
    prepareAuthState();
    console.log('=== Init done ===');
  });

  test('Run all test scripts', async () => {
    test.setTimeout(30 * 60 * 1000);
    const collector = new TestResultCollector();
    const configPath = createTempConfig();
    console.log('Temp config: ' + configPath);
    for (let i = 0; i < testConfig.testScripts.length; i++) {
      const script = testConfig.testScripts[i];
      const safeName = script.replace(/[\\\/]/g, '_').replace('.spec.ts', '');
      const jsonOutputPath = path.resolve(testConfig.outputDir, safeName + '-result.json');
      console.log('\n========== [' + (i + 1) + '/' + testConfig.testScripts.length + '] ' + script + ' ==========');
      const startTime = Date.now();
      const { exitCode, stderr } = await runScript(script, jsonOutputPath, configPath);
      console.log('Done | exit: ' + exitCode + ' | time: ' + ((Date.now() - startTime) / 1000).toFixed(1) + 's');
      if (stderr) fs.writeFileSync(path.join(testConfig.outputDir, safeName + '-stderr.log'), stderr);
      extractResults(jsonOutputPath, script, collector);
      if (collector.results.filter(r => r.scriptName === script).length === 0) {
        collector.add(script, exitCode === 0 ? 'passed' : 'failed', Date.now() - startTime, script, exitCode !== 0 ? 'exit ' + exitCode : undefined);
      }
    }
    try { fs.unlinkSync(configPath); } catch {}
    const s = collector.summary;
    console.log('\n=== Summary ===');
    console.log('Total: ' + s.total + ' Pass: ' + s.passed + ' Fail: ' + s.failed + ' Rate: ' + s.passRate);
    generateTestReport(collector);

    // Print report paths
    const midsceneReportPath = path.resolve(testConfig.midsceneReportDir);
    console.log('\n=== Reports ===');
    console.log('Midscene Report Dir: file:///' + midsceneReportPath.replace(/\\/g, '/'));
    console.log('Custom Report Dir: ' + path.resolve(testConfig.reportDir));
    console.log('All scripts done');
  });
});
