const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");

const PROJECT_ROOT = path.join(__dirname, "..");
const FLASK_PORT = 5001;
const FLASK_URL = `http://127.0.0.1:${FLASK_PORT}`;

let flaskProcess = null;
let mainWindow = null;

function startFlask() {
  flaskProcess = spawn("python", ["run_server.py"], {
    cwd: PROJECT_ROOT,
    stdio: "pipe",
  });

  flaskProcess.stdout.on("data", (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on("data", (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.on("close", (code) => {
    console.log(`[Flask] Process exited with code ${code}`);
    flaskProcess = null;
  });
}

function waitForFlask(retries = 30) {
  return new Promise((resolve, reject) => {
    let attempts = 0;

    const check = () => {
      attempts++;
      const req = http.get(`${FLASK_URL}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      });

      req.on("error", () => {
        retry();
      });

      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    };

    const retry = () => {
      if (attempts >= retries) {
        reject(new Error("Flask server did not start in time"));
      } else {
        setTimeout(check, 500);
      }
    };

    check();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(FLASK_URL);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function stopFlask() {
  if (flaskProcess) {
    flaskProcess.kill();
    flaskProcess = null;
  }
}

app.on("ready", async () => {
  startFlask();

  try {
    await waitForFlask();
  } catch (err) {
    console.error(err.message);
    app.quit();
    return;
  }

  createWindow();
});

app.on("window-all-closed", () => {
  stopFlask();
  app.quit();
});

app.on("before-quit", () => {
  stopFlask();
});
