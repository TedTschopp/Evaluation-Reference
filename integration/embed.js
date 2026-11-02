const frame=document.getElementById('evaluation-lab');
const lab=new URL(frame.dataset.src,location.href);
lab.searchParams.set('parent_origin',location.origin);
document.getElementById('exercise').addEventListener('toggle',function(){
 if(this.open&&!frame.hasAttribute('src')){frame.src=lab.href;frame.hidden=false;}
});
window.addEventListener('message',function(event){
 if(event.origin!==lab.origin||event.source!==frame.contentWindow||event.data?.type!=='eval-lab-height')return;
 const height=Number(event.data.height);
 if(Number.isFinite(height))frame.style.height=Math.max(700,Math.min(5000,height))+'px';
});
