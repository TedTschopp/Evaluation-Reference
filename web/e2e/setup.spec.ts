import {test,expect} from '@playwright/test';

test('static replay explains how to start live evaluation',async({page})=>{
 await page.route('**/api/health',route=>route.fulfill({status:404,contentType:'text/html',body:'<!DOCTYPE html><h1>Not found</h1>'}));
 await page.goto('./');
 await page.getByRole('button',{name:'Run it live'}).click();
 await expect(page.getByText('Replay works. Live mode needs the Python service.')).toBeVisible();
 await expect(page.locator('.live-panel pre')).toContainText('uv run --no-editable eval-lab serve');
 await page.getByRole('button',{name:'Use local Ollama',exact:true}).click();
 await expect(page.getByLabel('Base URL',{exact:true})).toHaveValue('http://localhost:11434');
 await expect(page.getByLabel('Model identifier',{exact:true})).toHaveValue('llama3.2:3b');
 await expect(page.getByRole('combobox',{name:'Authentication',exact:true})).toHaveValue('none');
 await expect(page.getByRole('button',{name:'Test connection and tools'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Run 1 evaluation',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Replay the lesson'}).click();
 await expect(page.locator('.answer-text')).toContainText('Twelve');
});

test('local service, tool probe, and optional judge have clear prerequisites',async({page})=>{
 await page.route('**/api/health',route=>route.fulfill({json:{status:'ok',version:'1.2.0',hosted:false,protocols:['ollama','openai_chat_completions']}}));
 await page.route('**/api/connections/test',route=>route.fulfill({json:{connected:true,tools:true,message:'Function calling verified.'}}));
 await page.goto('./');await page.getByRole('button',{name:'Run it live'}).click();
 await expect(page.getByText('Local evaluation service connected',{exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Use local Ollama',exact:true}).click();
 await page.getByRole('button',{name:'Test connection and tools'}).click();
 await expect(page.getByRole('button',{name:'Run 1 evaluation',exact:true})).toBeEnabled();
 await page.getByText('Optional independent AI judge',{exact:true}).click();
 await page.getByLabel('Add an AI judge to this run').check();
 await expect(page.getByRole('button',{name:'Run 1 evaluation',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Use local Ollama for judge'}).click();
 await expect(page.getByRole('button',{name:'Run 1 evaluation',exact:true})).toBeEnabled();
 await page.getByRole('group',{name:'Document agent',exact:true}).getByLabel('Base URL',{exact:true}).fill('http');
 await expect(page.getByRole('button',{name:'Test connection and tools'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Run 1 evaluation',exact:true})).toBeDisabled();
});

test('an imported run can be cleared without reimporting its file',async({page})=>{
 await page.goto('./');await expect(page.getByRole('heading',{level:1})).toHaveText('Did it answer the question?');
 await page.locator('input[type=file]').first().setInputFiles('../examples/runs/with-judge.json');
 await expect(page.getByText('Viewing an imported result; it has not been rerun.')).toBeVisible();
 await page.getByRole('button',{name:'Return to bundled examples'}).click();
 await expect(page.getByText('Viewing an imported result; it has not been rerun.')).toHaveCount(0);
 await expect(page.locator('.context-bar')).toContainText('Replay · authored examples');
 await page.getByRole('navigation',{name:'Guided lessons'}).getByRole('button',{name:'Define the job'}).click();
 await expect(page.locator('.answer-text')).toContainText('Twelve');
});
