const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const assert=require('node:assert/strict');
const path=require('node:path');
const {PDFDocument,StandardFonts}=require('../site/vendor/pdf-lib.js');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN||undefined});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.TEST_URL||'http://localhost:8765');
 await page.getByRole('button',{name:'工作事项',exact:true}).click();await page.locator('#tasksSample').click();assert.equal(await page.locator('#taskList .card').count(),1);
 await page.locator('#taskFilter').selectOption('done');assert.equal(await page.locator('#taskList .card').count(),0);
 await page.getByRole('button',{name:'访谈准备',exact:true}).click();await page.locator('#question').fill('请举一个具体例子？');await page.locator('#addQuestion').click();assert.equal(await page.locator('#questionList .card').count(),1);
 await page.getByRole('button',{name:'来源知识库',exact:true}).click();await page.locator('#sourceId').fill('demo:001');await page.locator('#noteTitle').fill('虚构测试');await page.locator('#claim').fill('<script>bad</script>');await page.locator('#addNote').click();assert.equal(await page.locator('#noteList .card').count(),1);assert((await page.locator('#noteList').textContent()).includes('<script>'));
 await page.getByRole('button',{name:'周课表',exact:true}).click();
 const c={name:'虚构课程',code:'DEMO',section:'01',credit:2,day:1,start:1,end:2,weeks:'1-16单',teacher:'测试',room:'测试',nature:'待确认',eligibility:'待确认',exam:'待确认'};
 await page.locator('#coursesImport').setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify([c,{...c,day:2}]))});
 await page.waitForFunction(()=>document.querySelector('#creditAudit').textContent.includes('= 2'));assert.equal(await page.locator('#calendar .event strong').count(),2);
 await page.locator('#week').fill('2');assert.equal(await page.locator('#calendar .event').count(),0);
 await page.locator('#coursesImport').setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify([c,{...c,code:'OTHER',section:'02',online:true}]))});await page.waitForFunction(()=>document.querySelectorAll('#conflicts .conflict').length===1);
 await page.getByRole('button',{name:'讲义打印',exact:true}).click();
 const pdf=await PDFDocument.create(),font=await pdf.embedFont(StandardFonts.Helvetica);for(let i=1;i<=3;i++){const p=pdf.addPage([400,600]);p.drawText('Synthetic Page '+i,{x:30,y:400,font,size:20});}
 await page.locator('#pdf').setInputFiles({name:'fixture.pdf',mimeType:'application/pdf',buffer:Buffer.from(await pdf.save())});
 const wait=page.waitForEvent('download');await page.locator('#makePdf').click();const download=await wait;const out=path.join(process.env.QA_DIR||'/private/tmp','workbench-print-test.pdf');await download.saveAs(out);
 const result=await PDFDocument.load(await fs.readFile(out));assert.equal(result.getPageCount(),2);assert(Math.abs(result.getPage(0).getWidth()-841.89)<1);assert.equal(errors.length,0,errors.join('\n'));
 if(process.env.QA_SCREENSHOT){await page.getByRole('button',{name:'周课表',exact:true}).click();await page.screenshot({path:process.env.QA_SCREENSHOT,fullPage:true});}
 console.log('Browser: tasks, interview, source cards, weekly filtering, credit dedup, conflicts, PDF export passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
