import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./e2e',timeout:30000,workers:1,reporter:'list',
 use:{baseURL:process.env.LAB_BASE_URL||'http://127.0.0.1:5174',channel:'chrome',headless:true,viewport:{width:1440,height:1000}},
 outputDir:'../test-results',
});

