import {test,expect} from '@playwright/test';

test('replay, guides, fonts, and embeds stay within this installation',async({page})=>{
 const requests:string[]=[];
 page.on('request',request=>requests.push(request.url()));
 await page.goto('./');
 await expect(page.getByRole('heading',{level:1})).toHaveText('Did it answer the question?');
 const installation=new URL(page.url());
 for(const name of ['Follow the evidence','Change the boundary','Test the grader','Compare versions','Decide what can ship']){
  await page.getByRole('navigation',{name:'Guided lessons'}).getByRole('button',{name}).click();
 }
 await page.getByRole('button',{name:/^(Download reference|Reference materials)$/}).click();
 const dialog=page.getByRole('dialog');
 const href=await dialog.getByRole('link',{name:'Instructor guide',exact:true}).getAttribute('href');
 expect(href).toBe('./docs/instructor-guide.html');
 const guide=await page.request.get(new URL(href!,installation).href);
 expect(guide.ok()).toBeTruthy();expect(await guide.text()).toContain('Instructor guide');
 await dialog.getByText('Embed this installation',{exact:true}).click();
 await dialog.getByLabel('Parent page origin').fill('https://blog.example');
 const code=await dialog.locator('pre').textContent();
 expect(code).toContain(new URL('./',installation).href+'?embed=1');
 expect(code).toContain('parent_origin=https%3A%2F%2Fblog.example');
 expect(requests.filter(url=>!url.startsWith(installation.origin+'/'))).toEqual([]);
 expect(requests.some(url=>url.endsWith('.woff2'))).toBeTruthy();
 await page.goto(new URL('integration/embed.html',new URL('./',installation)).href);
 await page.getByText('Interactive lab: inspect evidence, graders, and the release decision').click();
 await expect(page.frameLocator('#evaluation-lab').getByRole('heading',{level:1})).toHaveText('Did it answer the question?');
 await expect.poll(()=>page.locator('#evaluation-lab').evaluate(element=>element.style.height)).not.toBe('');
 const frameUrl=await page.locator('#evaluation-lab').getAttribute('src');
 expect(new URL(frameUrl!).searchParams.get('parent_origin')).toBe(installation.origin);
 expect(requests.filter(url=>!url.startsWith(installation.origin+'/'))).toEqual([]);
});
