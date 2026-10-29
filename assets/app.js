(()=>{'use strict';
const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
document.addEventListener('DOMContentLoaded',()=>{
 const date=$('#today');
 if(date){try{date.textContent=new Intl.DateTimeFormat('ar-IQ',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date())}catch(e){date.textContent='التاسعة نيوز'}}
 const menu=$('#menuBtn'),nav=$('#nav');
 menu?.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))});
 const status=$('#interactionStatus');
 const navLinks=$('#nav a[data-nav]');
 const filterables=$('.news-card,.small-story');
 navLinks.forEach(link=>link.addEventListener('click',e=>{
   const key=link.dataset.nav;
   if(key==='reports'||key==='video'){return}
   e.preventDefault();
   navLinks.forEach(a=>a.classList.toggle('active',a===link));
   filterables.forEach(el=>el.hidden=false);
   if(key==='home'||key==='all'){
     if(status)status.textContent='';
     window.scrollTo({top:key==='home'?0:$('#iraq')?.offsetTop||0,behavior:'smooth'});
     return;
   }
   if(key==='photos'){
     if(status)status.textContent='قسم الصور غير مضاف بعد؛ ستتم إضافته عند توفير صور منشورة خاصة بالموقع.';
     return;
   }
   const matches=filterables.filter(el=>(el.querySelector('.category')?.textContent||'').trim()===key);
   if(matches.length){
     filterables.forEach(el=>el.hidden=!matches.includes(el));
     if(status)status.textContent='عرض أخبار قسم '+key+' ('+matches.length+')';
     $('#iraq')?.scrollIntoView({behavior:'smooth',block:'start'});
   }else{
     if(status)status.textContent='لا توجد أخبار منشورة حالياً ضمن قسم '+key+'.';
   }
 }));
 const form=$('#search'),input=$('#searchInput');
 form?.addEventListener('submit',e=>{e.preventDefault();const q=(input?.value||'').trim().toLocaleLowerCase('ar');const cards=$$('.news-card,.small-story,.important li,.report-row,.video-grid a');let found=0;cards.forEach(el=>{const match=!q||el.textContent.toLocaleLowerCase('ar').includes(q);el.hidden=!match;if(match)found++});let note=$('#searchResult');if(!note){note=document.createElement('p');note.id='searchResult';note.className='search-result';form.insertAdjacentElement('afterend',note)}note.textContent=q?('نتائج البحث عن «'+q+'»: '+found):'تم عرض الأخبار كافة';if(q)note.scrollIntoView({behavior:'smooth',block:'center'})});
 input?.addEventListener('input',()=>{if(!input.value.trim()){$$('.news-card,.small-story,.important li,.report-row,.video-grid a').forEach(el=>el.hidden=false);const note=$('#searchResult');if(note)note.textContent=''}});
 $$('img').forEach(img=>{img.loading='lazy';img.addEventListener('error',()=>{if(!img.dataset.fallback){img.dataset.fallback='1';img.src='assets/news-placeholder.svg'}},{once:true})});
 const track=$('#tickerTrack');if(track){const clone=track.innerHTML;track.innerHTML=clone+clone}
 const up=document.createElement('button');up.className='back-top';up.type='button';up.textContent='↑';up.setAttribute('aria-label','العودة إلى الأعلى');document.body.appendChild(up);window.addEventListener('scroll',()=>{up.classList.toggle('visible',window.scrollY>450)});up.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
});
})();