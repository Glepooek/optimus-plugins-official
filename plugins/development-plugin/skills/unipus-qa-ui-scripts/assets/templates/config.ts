import fs from "fs";
import path from "path";

interface AuthConfig {
  loginUrl: string;
  username: string;
  password: string;
  usernameUnregistered: string;
  passwordUnregistered: string;
  usernameAdmin: string;
  passwordAdmin: string;
}

interface PagesConfig {
  [key: string]: string;
}

interface EnvironmentConfig {
  auth: AuthConfig;
  pages: PagesConfig;
}

interface EnvironmentsConfig {
  [env: string]: EnvironmentConfig;
}

class ConfigManager {
  private config: EnvironmentsConfig;
  private currentEnv: string;

  constructor() {
    const configPath = path.join(process.cwd(), "config", "environments.json");
    this.config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    this.currentEnv = process.env.TEST_ENV || "test";
  }

  getConfig(): EnvironmentConfig {
    const envConfig = this.config[this.currentEnv];
    if (!envConfig) {
      throw new Error(`Environment "${this.currentEnv}" not found in environments.json`);
    }
    return envConfig;
  }

  setEnvironment(env: string): void {
    this.currentEnv = env;
  }

  getCurrentEnv(): string {
    return this.currentEnv;
  }
}

export const configManager = new ConfigManager();
