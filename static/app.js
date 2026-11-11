"use strict";
const $ = selector => document.querySelector(selector);
const state = { session: null, csrf: "", results: null, view: "search", authMode: "login", lang: localStorage.getItem("waypoint-language") === "ar" ? "ar" : "en" };
const words = {
en: { skip:"Skip to content", explore:"Explore flights", alerts:"Price alerts", about:"The project", signin:"Sign in", signout:"Sign out", eyebrow:"LESS GUESSWORK. MORE GOING.", headline:"A better\nway there.", description:"Find the flight that fits your plans.\nKeep an eye on the price. Go when it feels right.", tag1:"Made for your next departure", arttitle:"Your plans, taking shape.", artbody:"One good flight changes everything.", searchtitle:"Where are we heading?", oneway:"One way · Total fares in AED", from:"FROM", to:"TO", departure:"DEPARTURE", travellers:"ADULTS", search:"Find flights", direct:"Nonstop only", budget:"Total budget", airline:"Airline", any:"Any airline", cabin:"Cabin", economy:"Economy", premium:"Premium economy", business:"Business", first:"First", airporthelp:"Use a three-letter airport code. Prices are totals for all selected adults.", aiprompt:"Have a trip in mind? Describe it instead.", optional:"OPTIONAL AI INPUT", triplabel:"Describe your trip", aiexample:"Dubai to Cairo next Friday, nonstop, under AED 1,500", fillform:"Fill my search", ainote:"AI fills the form only. Review the airports and date before searching.", feature1:"See the tradeoffs.", feature1body:"Compare price, travel time and stops together. The cheapest flight is only part of the story.", feature2:"Let the price come to you.", feature2body:"Set a target fare. We check on a schedule and email you when a matching price is found.", feature3:"Know where you stand.", feature3body:"See when fares were checked. Continue your search externally; confirm the final fare before payment.", watchlist:"YOUR TRAVEL WATCHLIST", alerttitle:"Good things\nare worth watching.", underthehood:"UNDER THE HOOD", abouttitle:"Built with\nreal-world care.", aboutbody:"Waypoint is a flight discovery engineering project: real provider integration, isolated accounts, verified email alerts, bounded API usage, and an optional AI trip parser. Booking and payment happen outside this application.", privacytitle:"Your data, your choice.", privacybody:"We store your email, password hash, sessions and saved alerts. Flight searches are cached for 10 minutes. Search details go to the flight provider. If you use AI input, that text goes to OpenAI. Email is delivered through the configured mail service. We do not collect payment cards or passport details. Delete your account to remove your saved data; backup copies expire under the operator's retention policy.", limitstitle:"Clear boundaries.", limitsbody:"Fares can change and are not reservations. Baggage and fare rules must be confirmed with the seller. The external link opens a route search, not a guaranteed offer or an affiliated checkout. Waypoint cannot issue, cancel or refund tickets.", deleteaccount:"Delete my account and alerts", footer:"A little clarity before you take off.", footernote:"Flight discovery · No ticket sales", email:"Email address", password:"Password · 12+ characters", forgot:"Forgot password?", pricewatch:"PRICE WATCH", savealerttitle:"Wait for your kind of fare.", target:"Target total price · AED", alertnote:"Up to 3 active alerts. Verified email required. A matching fare is not a guaranteed booking.", savealert:"Create price alert", demobanner:"DEMO MODE · Illustrative fares, not live availability. No reservations or real price monitoring.", unavailable:"Live search is not configured. You can explore the interface; searches require a provider connection.", localmail:"Development email delivery: messages are saved to the local outbox, not sent.", searchfirst:"Run a search to compare flight options.", loading:"Checking the flight board…", matches:"flight options", checked:"Checked", cached:"cached up to 10 min", sortprice:"Lowest price", sortduration:"Shortest trip", watch:"Watch this route", nonstop:"Nonstop", stops:"stop(s)", bestprice:"LOWEST FARE", fastest:"SHORTEST", total:"total for all adults", onward:"Continue on Google Flights ↗", onwardnote:"Opens a new route search. Final fares, baggage, payment and ticketing are confirmed externally. No booking is made here.", noflights:"No matching flights this time.", noflightsbody:"Try another date, a higher budget, or fewer filters. You can still watch this route.", signinbody:"Sign in to search and manage your own price alerts.", welcome:"Welcome back.", registertitle:"A new departure.", registerbody:"Create your account. Verify your email to receive price alerts.", register:"Create account", needaccount:"New here? Create an account", haveaccount:"Already registered? Sign in", forgottitle:"Let's get you back.", forgotbody:"Enter your email to request a password reset link.", sendreset:"Send reset link", resettitle:"A fresh start.", resetbody:"Choose a new password. Existing sessions will be signed out.", resetbutton:"Change password", signinsuccess:"Signed in. Your next trip is waiting.", needlogin:"Sign in to continue.", networkerror:"We could not reach the service. Please try again.", updatedform:"Search filled. Check the details, then find flights.", ainotconfigured:"AI input is not configured. You can use the regular search form.", emptyalerts:"Your watchlist is clear.", emptyalertsbody:"Search for a route, then choose Watch this route to set your target fare.", alertdescription:"Up to 3 active alerts. Checks every {hours} hours, subject to provider limits. Email notifications are sent when a target is first met or a lower matching fare is found.", verifyneeded:"Verify your email before creating alerts.", resend:"Resend verification", delete:"Delete", active:"Watching", expired:"Expired", lastchecked:"Last checked", pending:"Waiting for first check", checkfailed:"Last check failed; a retry is scheduled.", accountdeleted:"Account deleted.", deleteconfirm:"Delete your account and all saved alerts? This cannot be undone.", verifyconfirm:"Confirm email verification?", verificationdone:"Email verified. You can now create alerts.", working:"Working…", formerror:"Check your entries", signintoalerts:"Sign in to see your price alerts.", datehint:"All schedules shown in airport local time.", verified:"Email verified", notverified:"Email not verified", duration:"duration", sample:"ILLUSTRATIVE FARES", livesource:"LIVE PROVIDER RESULTS" },
ar: { skip:"انتقل إلى المحتوى", explore:"استكشف الرحلات", alerts:"تنبيهات الأسعار", about:"عن المشروع", signin:"تسجيل الدخول", signout:"تسجيل الخروج", eyebrow:"خيارات أوضح. رحلات أجمل.", headline:"طريق أجمل\nلوجهتك.", description:"اعثر على الرحلة التي تناسب خططك.\nتابع السعر، وانطلق في الوقت المناسب.", tag1:"لرحلتك القادمة", arttitle:"خططك تقترب من الإقلاع.", artbody:"رحلة مناسبة تصنع فرقًا.", searchtitle:"إلى أين ستكون الرحلة؟", oneway:"ذهاب فقط · الإجمالي بالدرهم", from:"من", to:"إلى", departure:"تاريخ المغادرة", travellers:"البالغون", search:"ابحث عن رحلة", direct:"دون توقف فقط", budget:"الميزانية الإجمالية", airline:"شركة الطيران", any:"كل الشركات", cabin:"درجة السفر", economy:"اقتصادية", premium:"اقتصادية ممتازة", business:"أعمال", first:"أولى", airporthelp:"استخدم رمز المطار من ثلاثة أحرف. الأسعار إجمالية لجميع البالغين المحددين.", aiprompt:"لديك رحلة في بالك؟ اكتب تفاصيلها.", optional:"إدخال اختياري بالذكاء الاصطناعي", triplabel:"صف رحلتك", aiexample:"من دبي للقاهرة الجمعة القادمة، دون توقف، بأقل من 1500 درهم", fillform:"تعبئة البحث", ainote:"الذكاء الاصطناعي يعبئ النموذج فقط. راجع المطارات والتاريخ قبل البحث.", feature1:"قارن الصورة كاملة.", feature1body:"شاهد السعر ومدة السفر والتوقفات معًا. السعر الأقل جزء من الاختيار، وليس كل شيء.", feature2:"دع السعر يأتي إليك.", feature2body:"حدد السعر المناسب. نفحص الرحلة دوريًا ونرسل بريدًا عند العثور على سعر يطابق هدفك.", feature3:"كل شيء أمامك بوضوح.", feature3body:"اطلع على وقت فحص الأسعار. أكمل البحث خارجيًا وتحقق من السعر النهائي قبل الدفع.", watchlist:"قائمة رحلاتك المراقبة", alerttitle:"رحلات تستحق\nالانتظار.", underthehood:"خلف التجربة", abouttitle:"هندسة تراعي\nالاستخدام الفعلي.", aboutbody:"Waypoint مشروع هندسي لاكتشاف رحلات الطيران: تكامل مع مزود بيانات، حسابات مستقلة، تنبيهات لبريد موثق، حدود لاستهلاك الخدمات، ومحلل اختياري للطلبات بالذكاء الاصطناعي. يتم الحجز والدفع خارج التطبيق.", privacytitle:"بياناتك تحت سيطرتك.", privacybody:"نحفظ بريدك وبصمة كلمة المرور والجلسات والتنبيهات. نخزن نتائج البحث مؤقتًا لعشر دقائق ونرسل تفاصيل البحث لمزود الرحلات. عند استخدام الإدخال الذكي، يُرسل نصه إلى OpenAI. يُرسل البريد عبر خدمة المشغل. لا نجمع بطاقات الدفع أو جوازات السفر. يمكنك حذف الحساب والبيانات المرتبطة به؛ تنتهي النسخ الاحتياطية وفق سياسة احتفاظ المشغل.", limitstitle:"حدود واضحة.", limitsbody:"الأسعار قابلة للتغيير وليست حجوزات. تحقق من الأمتعة وشروط التذكرة لدى البائع. الرابط الخارجي يفتح بحثًا للمسار ولا يضمن عرضًا محددًا أو شراكة تجارية. لا يصدر Waypoint التذاكر ولا يلغيها أو يسترد قيمتها.", deleteaccount:"حذف حسابي وتنبيهاتي", footer:"رؤية أوضح قبل الإقلاع.", footernote:"اكتشاف رحلات · دون بيع تذاكر", email:"البريد الإلكتروني", password:"كلمة المرور · 12 حرفًا على الأقل", forgot:"نسيت كلمة المرور؟", pricewatch:"مراقبة السعر", savealerttitle:"انتظر السعر المناسب لك.", target:"السعر الإجمالي المستهدف · درهم", alertnote:"حتى 3 تنبيهات نشطة. يلزم توثيق البريد. العثور على سعر لا يضمن إمكانية الحجز.", savealert:"إنشاء تنبيه سعر", demobanner:"وضع تجريبي · أسعار توضيحية وليست نتائج حية. لا توجد حجوزات أو مراقبة أسعار حقيقية.", unavailable:"البحث الحي غير مهيأ. يمكنك استكشاف الواجهة، لكن البحث يتطلب ربط مزود بيانات.", localmail:"البريد في وضع التطوير: تحفظ الرسائل محليًا ولا تُرسل فعليًا.", searchfirst:"ابحث عن مسار لمقارنة خيارات الطيران.", loading:"جارٍ البحث عن الرحلات…", matches:"خيارات طيران", checked:"آخر فحص", cached:"تخزين مؤقت حتى 10 دقائق", sortprice:"الأقل سعرًا", sortduration:"الأقصر مدة", watch:"راقب هذا المسار", nonstop:"دون توقف", stops:"توقف", bestprice:"أقل سعر", fastest:"أقصر رحلة", total:"الإجمالي لكل البالغين", onward:"متابعة على Google Flights ↗", onwardnote:"يفتح بحثًا جديدًا للمسار. يتحقق الموقع الخارجي من السعر والأمتعة والدفع وإصدار التذكرة. لا يتم الحجز هنا.", noflights:"لا توجد رحلات تطابق الشروط.", noflightsbody:"جرب تاريخًا آخر أو ميزانية أعلى أو فلاتر أقل. يمكنك متابعة سعر هذا المسار.", signinbody:"سجل الدخول للبحث وإدارة تنبيهات أسعارك الخاصة.", welcome:"أهلًا بعودتك.", registertitle:"بداية رحلة جديدة.", registerbody:"أنشئ حسابك، ووثق بريدك لتلقي تنبيهات الأسعار.", register:"إنشاء حساب", needaccount:"مستخدم جديد؟ أنشئ حسابًا", haveaccount:"لديك حساب؟ سجل الدخول", forgottitle:"لنعد إلى حسابك.", forgotbody:"أدخل بريدك لطلب رابط إعادة تعيين كلمة المرور.", sendreset:"إرسال رابط الاستعادة", resettitle:"بداية آمنة.", resetbody:"اختر كلمة مرور جديدة. ستُلغى الجلسات السابقة.", resetbutton:"تغيير كلمة المرور", signinsuccess:"تم تسجيل الدخول. رحلتك القادمة تنتظرك.", needlogin:"سجل الدخول للمتابعة.", networkerror:"تعذر الاتصال بالخدمة. حاول مجددًا.", updatedform:"تمت تعبئة البحث. راجع التفاصيل ثم ابحث عن الرحلات.", ainotconfigured:"الإدخال الذكي غير مهيأ. يمكنك استخدام نموذج البحث المعتاد.", emptyalerts:"قائمة المتابعة فارغة.", emptyalertsbody:"ابحث عن مسار، ثم اختر مراقبته وحدد السعر المستهدف.", alertdescription:"حتى 3 تنبيهات نشطة. فحص كل {hours} ساعة وفق حدود المزود. نرسل بريدًا عند تحقق السعر المستهدف أول مرة أو العثور لاحقًا على سعر مطابق أقل.", verifyneeded:"وثق بريدك قبل إنشاء تنبيهات.", resend:"إعادة إرسال التوثيق", delete:"حذف", active:"قيد المراقبة", expired:"منتهٍ", lastchecked:"آخر فحص", pending:"بانتظار أول فحص", checkfailed:"تعذر الفحص الأخير؛ تمت جدولة المحاولة التالية.", accountdeleted:"تم حذف الحساب.", deleteconfirm:"هل تريد حذف حسابك وكل تنبيهاتك؟ لا يمكن التراجع عن ذلك.", verifyconfirm:"تأكيد توثيق البريد الإلكتروني؟", verificationdone:"تم توثيق البريد. يمكنك إنشاء التنبيهات الآن.", working:"جارٍ التنفيذ…", formerror:"راجع البيانات المدخلة", signintoalerts:"سجل الدخول للاطلاع على تنبيهات الأسعار.", datehint:"المواعيد بالتوقيت المحلي لكل مطار.", verified:"البريد موثق", notverified:"البريد غير موثق", duration:"مدة الرحلة", sample:"أسعار توضيحية", livesource:"نتائج مزود الرحلات" }
};
Object.assign(words.en, {
  emailrequired:"Enter your email address.", emailinvalid:"Enter a valid email address.",
  passwordrequired:"Enter your password.", passwordshort:"Use at least 12 characters. You entered {count}.",
  passwordlong:"Use no more than 128 characters.", passwordcount:"{count} / 12 characters minimum",
  confirmpassword:"Confirm password", confirmrequired:"Enter your password again.",
  confirmmismatch:"The passwords do not match.", showpassword:"Show password", hidepassword:"Hide password",
  registrationsubmitted:"Registration request received. Enter your password to sign in.",
  localverificationnote:"In this local version, verification messages are saved on this computer, not emailed. You can sign in and search without email verification; verification is required for price alerts only.",
  resetrequested:"If this account exists, a password reset message has been queued.",
  resetlocal:"If this account exists, its reset link will be saved in the local email outbox. No email is sent in this version.",
  resetchanged:"Password changed. Sign in with your new password.",
  invalidlogin:"Email or password is incorrect. Check both, or choose Forgot password.",
  authlimited:"Too many attempts. Wait before trying again; repeated attempts can extend the wait.",
  sessionexpired:"Your page session has expired. Refresh the page and try again.",
  authinvalid:"Check your email and use a password between 12 and 128 characters.",
  resetinvalid:"This reset link is invalid or expired. Request a new link.",
  authfailed:"We could not complete this request. Please try again."
});
Object.assign(words.ar, {
  emailrequired:"أدخل البريد الإلكتروني.", emailinvalid:"أدخل بريدًا إلكترونيًا صحيحًا.",
  passwordrequired:"أدخل كلمة المرور.", passwordshort:"كلمة المرور تحتاج 12 حرفًا على الأقل. أدخلت {count}.",
  passwordlong:"الحد الأقصى لكلمة المرور 128 حرفًا.", passwordcount:"{count} / 12 حرفًا كحد أدنى",
  confirmpassword:"تأكيد كلمة المرور", confirmrequired:"أعد إدخال كلمة المرور.",
  confirmmismatch:"كلمتا المرور غير متطابقتين.", showpassword:"إظهار كلمة المرور", hidepassword:"إخفاء كلمة المرور",
  registrationsubmitted:"تم استلام طلب التسجيل. أدخل كلمة المرور لتسجيل الدخول.",
  localverificationnote:"في هذه النسخة المحلية تُحفظ رسالة التوثيق على الجهاز ولا تُرسل إلى البريد. يمكنك تسجيل الدخول والبحث دون توثيق البريد؛ التوثيق مطلوب لتنبيهات الأسعار فقط.",
  resetrequested:"إذا كان الحساب موجودًا، تمت جدولة رسالة استعادة كلمة المرور.",
  resetlocal:"إذا كان الحساب موجودًا، سيُحفظ رابط الاستعادة في البريد المحلي على الجهاز. هذه النسخة لا ترسل بريدًا فعليًا.",
  resetchanged:"تم تغيير كلمة المرور. سجل الدخول بكلمة المرور الجديدة.",
  invalidlogin:"البريد أو كلمة المرور غير صحيحة. راجعهما أو اختر «نسيت كلمة المرور؟».",
  authlimited:"محاولات كثيرة. انتظر قبل المحاولة مجددًا؛ تكرار المحاولات قد يطيل الانتظار.",
  sessionexpired:"انتهت جلسة الصفحة. حدّث الصفحة وحاول مجددًا.",
  authinvalid:"راجع البريد واستخدم كلمة مرور من 12 إلى 128 حرفًا.",
  resetinvalid:"رابط الاستعادة غير صالح أو منتهي الصلاحية. اطلب رابطًا جديدًا.",
  authfailed:"تعذر إتمام الطلب. حاول مجددًا."
});
const t = key => words[state.lang][key] || words.en[key] || key;
const escapeHTML = text => String(text ?? "").replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[character]);
let toastTimer;
function toast(message, error=false) { const box=$("#toast"); box.textContent=message; box.dataset.error=String(error); box.hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>box.hidden=true,7000); }
async function api(path, options={}) {
  const controller = new AbortController();
  const timeout = setTimeout(()=>controller.abort(), 30000);
  try {
    const response=await fetch(path,{credentials:"same-origin",...options,signal:controller.signal,headers:{"Content-Type":"application/json","X-CSRF-Token":state.csrf,...options.headers}});
    const payload=await response.json();
    if(!response.ok) {
      if(path.startsWith("/api/auth/")) {
        const key=response.status===429?"authlimited":response.status===403?"sessionexpired":
          response.status===401?"invalidlogin":response.status===422?"authinvalid":
          path.endsWith("/reset")&&response.status===400?"resetinvalid":"authfailed";
        throw new Error(t(key));
      }
      const details=payload.errors?.map(entry=>`${entry.field}: ${entry.message}`).join(" · ");
      throw new Error(details || payload.detail || t("networkerror"));
    }
    return payload;
  } catch(error) { if(error instanceof TypeError || error.name==="AbortError") throw new Error(t("networkerror")); throw error; }
  finally { clearTimeout(timeout); }
}
async function busy(button, action) { if(button.disabled)return; button.disabled=true; try { await action(); } catch(error) { toast(error.message,true); } finally { button.disabled=false; } }
function applyLanguage() {
  document.documentElement.lang=state.lang; document.documentElement.dir=state.lang==="ar"?"rtl":"ltr";
  document.querySelectorAll("[data-i18n]").forEach(element=>{ const lines=t(element.dataset.i18n).split("\n"); element.replaceChildren(); lines.forEach((line,index)=>{if(index)element.append(document.createElement("br"));element.append(document.createTextNode(line));}); });
  document.querySelectorAll("[data-placeholder]").forEach(element=>element.placeholder=t(element.dataset.placeholder));
  $("#language").textContent=state.lang==="en"?"العربية":"English";
  renderSession(); if(state.results)renderResults(); if(state.view==="alerts")loadAlerts();
}
function renderSession() {
  if(!state.session)return;
  const session=state.session;
  $("#account").textContent=t(session.user?"signout":"signin");
  $("#account").title=session.user?.email || "";
  $("#account-tools").hidden=!session.user;
  const banners=[];
  if(session.demo)banners.push(t("demobanner"));
  if(!session.search_available)banners.push(t("unavailable"));
  if(session.email_delivery==="local-outbox")banners.push(t("localmail"));
  $("#mode-banner").textContent=banners.join(" · "); $("#mode-banner").hidden=!banners.length;
  $("#ai-note").textContent=t(session.ai_available?"ainote":"ainotconfigured");
  $("#interpret").disabled=!session.ai_available;
  $("#alert-description").textContent=t("alertdescription").replace("{hours}",session.alert_interval_hours);
}
async function refreshSession() { state.session=await api("/api/session"); state.csrf=state.session.csrf;renderSession(); }
function requireUser() { if(state.session?.user)return true;openAuth("login");return false; }
function showView(view) { state.view=view; for(const name of ["search","alerts","about"])$(`#${name}-view`).hidden=name!==view;document.querySelectorAll("[data-view]").forEach(button=>button.classList.toggle("selected",button.dataset.view===view));if(view==="alerts")loadAlerts(); }
function authFeedback(message, error=false) {
  const feedback=$("#auth-feedback");feedback.textContent=message;feedback.dataset.error=String(error);
}
function clearAuthErrors() {
  for(const name of ["email","password","confirm-password"]) {
    $(`#auth-${name}`).removeAttribute("aria-invalid");
    $(`#auth-${name}-error`).textContent="";
  }
}
function authFieldError(name, message) {
  const field=$(`#auth-${name}`);field.setAttribute("aria-invalid","true");
  $(`#auth-${name}-error`).textContent=message;
}
function passwordCount() {
  const count=Array.from($("#auth-password").value).length;
  $("#auth-password-help").textContent=t("passwordcount").replace("{count}",count);
}
function validateAuth() {
  clearAuthErrors();authFeedback("");$("#toast").hidden=true;
  const email=$("#auth-email"),password=$("#auth-password"),mode=state.authMode;
  if(mode!=="reset") {
    if(!email.value.trim())authFieldError("email",t("emailrequired"));
    else if(!email.validity.valid)authFieldError("email",t("emailinvalid"));
  }
  if(mode!=="forgot") {
    const length=Array.from(password.value).length;
    if(!length)authFieldError("password",t("passwordrequired"));
    else if(length<12)authFieldError("password",t("passwordshort").replace("{count}",length));
    else if(length>128)authFieldError("password",t("passwordlong"));
  }
  if(mode==="register") {
    const confirmation=$("#auth-confirm-password").value;
    if(!confirmation)authFieldError("confirm-password",t("confirmrequired"));
    else if(confirmation!==password.value)authFieldError("confirm-password",t("confirmmismatch"));
  }
  const invalid=$("#auth-form [aria-invalid=true]");
  if(invalid){invalid.focus();return false;}
  return true;
}
function openAuth(mode) {
  state.authMode=mode;
  const config={login:["welcome","signinbody","signin"],register:["registertitle","registerbody","register"],forgot:["forgottitle","forgotbody","sendreset"],reset:["resettitle","resetbody","resetbutton"]}[mode];
  $("#auth-title").textContent=t(config[0]);$("#auth-description").textContent=t(config[1]);$("#auth-submit").textContent=t(config[2]);
  if(mode==="register" && state.session?.email_delivery==="local-outbox") {
    $("#auth-description").textContent+=" "+t("localverificationnote");
  }
  clearAuthErrors();authFeedback("");$("#auth-password").value="";$("#auth-password").type="password";
  $("#auth-confirm-password").value="";$("#confirm-password-label").hidden=mode!=="register";
  $("#auth-confirm-password").required=mode==="register";
  $("#toggle-password").textContent=t("showpassword");$("#toggle-password").setAttribute("aria-pressed","false");
  $("#password-label").hidden=mode==="forgot";$("#auth-password").required=mode!=="forgot";
  $("#auth-email").closest(".auth-field").hidden=mode==="reset";$("#auth-email").required=mode!=="reset";
  $("#auth-password").autocomplete=mode==="login"?"current-password":"new-password";
  $("#auth-switch").textContent=t(mode==="login"?"needaccount":"haveaccount");
  $("#forgot-password").hidden=mode!=="login";
  passwordCount();
  if(!$("#auth-dialog").open)$("#auth-dialog").showModal();
  (mode==="reset"?$("#auth-password"):$("#auth-email")).focus();
}
function searchQuery() {return {origin:$("#origin").value.toUpperCase().trim(),destination:$("#destination").value.toUpperCase().trim(),departure:$("#departure").value,adults:Number($("#adults").value),direct:$("#direct").checked,budget:$("#budget").value?Number($("#budget").value):null,airline:$("#airline").value,cabin:$("#cabin").value};}
function fillQuery(query) {for(const field of ["origin","destination","departure","adults","budget","airline","cabin"])$(`#${field}`).value=query[field]??"";$("#direct").checked=query.direct;}
function duration(minutes) {return `${Math.floor(minutes/60)}h ${minutes%60}m`;}
function money(price) {return new Intl.NumberFormat(state.lang==="ar"?"ar-AE":"en-AE",{maximumFractionDigits:0}).format(price);}
function timestamp(iso) {return new Date(iso).toLocaleString(state.lang==="ar"?"ar-AE":"en-GB",{dateStyle:"medium",timeStyle:"short"});}
function timePart(localTime) {return String(localTime).split(" ").at(-1);}
function renderResults() {
  const response=state.results;
  const query=response.query;
  const flights=[...response.flights];
  if(state.sort==="duration")flights.sort((a,b)=>a.duration-b.duration);
  const minimum=Math.min(...flights.map(flight=>flight.price));
  const quickest=Math.min(...flights.map(flight=>flight.duration));
  const cards=flights.map(flight=>{
    const first=flight.segments[0],last=flight.segments.at(-1);
    const tags=(flight.price===minimum?`<span class="fare-tag">${t("bestprice")}</span>`:"")+(flight.duration===quickest?`<span class="fare-tag">${t("fastest")}</span>`:"");
    return `<article class="flight-card"><div class="flight-brand"><span class="airline-mark" aria-hidden="true">${escapeHTML(first.flight_number.slice(0,2)||"✈")}</span><div><strong>${escapeHTML(first.airline)}</strong><small>${escapeHTML(first.flight_number)}</small><div class="fare-tags">${tags}</div></div></div><div class="itinerary"><div><b>${escapeHTML(timePart(first.departure))}</b><small>${escapeHTML(first.origin)}</small></div><div class="flight-path">${escapeHTML(duration(flight.duration))}<span class="path-line"></span>${flight.stops?`${flight.stops} ${t("stops")}`:t("nonstop")}</div><div><b>${escapeHTML(timePart(last.arrival))}</b><small>${escapeHTML(last.destination)} · ${escapeHTML(last.arrival.split(" ")[0])}</small></div></div><div class="flight-price"><strong><small>AED</small>${money(flight.price)}</strong><small>${t("total")}</small></div></article>`;
  }).join("");
  $("#results").innerHTML=`<div class="results-top"><div><p class="eyebrow">${t(response.demo?"sample":"livesource")}</p><h2>${escapeHTML(query.origin)} → ${escapeHTML(query.destination)} <small> / ${flights.length} ${t("matches")}</small></h2><p>${t("checked")} ${escapeHTML(timestamp(response.searched_at))} ${response.cached?`· ${t("cached")}`:""}</p></div><div class="results-actions"><label class="sr-only" for="sort-results">${t("duration")}</label><select id="sort-results"><option value="price">${t("sortprice")}</option><option value="duration">${t("sortduration")}</option></select><button class="button secondary" id="watch-route">${t("watch")}</button></div></div>${cards||`<div class="empty-state"><h3>${t("noflights")}</h3><p>${t("noflightsbody")}</p></div>`}<p class="results-note">${t("datehint")}</p>${response.demo?"":`<a class="button secondary" href="${escapeHTML(response.onward_url)}" target="_blank" rel="noopener noreferrer">${t("onward")}</a><p class="results-note">${t("onwardnote")}</p>`}`;
  $("#sort-results").value=state.sort||"price";
  $("#sort-results").onchange=event=>{state.sort=event.target.value;renderResults();};
  $("#watch-route").onclick=()=>{if(!requireUser())return;if(!state.session.user.verified){showView("alerts");toast(t("verifyneeded"),true);return;}$("#alert-route").textContent=`${query.origin} → ${query.destination} · ${query.departure} · ${query.adults}`;$("#target-price").value=query.budget|| (flights.length?Math.floor(minimum*.9):1000);$("#alert-dialog").showModal();};
}
async function loadAlerts() {
  if(!state.session?.user){$("#alert-list").innerHTML=`<div class="empty-state"><h3>${t("signintoalerts")}</h3><button class="button" id="alerts-login">${t("signin")}</button></div>`;$("#alerts-login").onclick=()=>openAuth("login");return;}
  try {
    const response=await api("/api/alerts");
    const verification=state.session.user.verified?"":`<div class="verification">${t("verifyneeded")}<button class="text-button" id="resend">${t("resend")}</button></div>`;
    $("#alert-list").innerHTML=verification+(response.alerts.length?response.alerts.map(alert=>`<article class="alert-card"><div><strong>${escapeHTML(alert.query.origin)} → ${escapeHTML(alert.query.destination)}</strong><p>${escapeHTML(alert.query.departure)} · AED ${money(alert.target_price)} · ${t(alert.active?"active":"expired")}</p><p>${alert.last_checked?`${t("lastchecked")}: ${escapeHTML(timestamp(alert.last_checked*1000))}${alert.last_price?` · AED ${money(alert.last_price)}`:""}`:t("pending")}</p>${alert.last_error?`<p>${t("checkfailed")}</p>`:""}</div><button class="text-button" data-delete-alert="${alert.id}">${t("delete")}</button></article>`).join(""):`<div class="empty-state"><h3>${t("emptyalerts")}</h3><p>${t("emptyalertsbody")}</p><button id="back-search" class="button secondary">${t("explore")}</button></div>`);
    $("#back-search")?.addEventListener("click",()=>showView("search"));
    $("#resend")?.addEventListener("click",event=>busy(event.target,async()=>{const response=await api("/api/auth/resend",{method:"POST"});toast(response.message);}));
    document.querySelectorAll("[data-delete-alert]").forEach(button=>button.onclick=()=>busy(button,async()=>{await api(`/api/alerts/${button.dataset.deleteAlert}`,{method:"DELETE"});await loadAlerts();}));
  }catch(error){toast(error.message,true);}
}
$("#search-form").addEventListener("submit",event=>{event.preventDefault();if(!requireUser())return;busy($("#search-form button[type=submit]"),async()=>{
  $("#results").setAttribute("aria-busy","true");$("#results").innerHTML=`<div class="loading-state">${t("loading")}</div>`;
  try{state.results=await api("/api/search",{method:"POST",body:JSON.stringify(searchQuery())});state.sort="price";renderResults();$("#principles").hidden=true;}
  catch(error){state.results=null;$("#results").replaceChildren();throw error;}finally{$("#results").setAttribute("aria-busy","false");}
});});
$("#auth-form").addEventListener("submit",event=>{
  event.preventDefault();if(!validateAuth())return;
  busy($("#auth-submit"),async()=>{
    const mode=state.authMode,button=$("#auth-submit"),label=button.textContent;
    const payload=mode==="reset"?{token:state.resetToken,password:$("#auth-password").value}:
      {email:$("#auth-email").value.trim(),...(mode!=="forgot"?{password:$("#auth-password").value}:{})};
    $("#auth-switch").disabled=true;$("#forgot-password").disabled=true;
    button.textContent=t("working");$("#auth-form").setAttribute("aria-busy","true");
    try {
      await api(`/api/auth/${mode}`,{method:"POST",body:JSON.stringify(payload)});
      if(mode==="login") {
        await refreshSession();$("#auth-dialog").close();toast(t("signinsuccess"));
        $("#auth-password").value="";if(state.view==="alerts")loadAlerts();
      } else if(mode==="register") {
        $("#auth-email").value=payload.email;
        openAuth("login");toast(t("registrationsubmitted"));
        $("#auth-password").focus();
      } else if(mode==="reset") {
        state.resetToken=null;openAuth("login");authFeedback(t("resetchanged"));
      } else authFeedback(t(state.session?.email_delivery==="local-outbox"?"resetlocal":"resetrequested"));
    } catch(error) {authFeedback(error.message,true);}
    finally {
      $("#auth-switch").disabled=false;$("#forgot-password").disabled=false;
      $("#auth-form").setAttribute("aria-busy","false");
      if(state.authMode===mode)button.textContent=label;
    }
  });
});
$("#auth-password").addEventListener("input",passwordCount);
for(const name of ["email","password","confirm-password"]) {
  $(`#auth-${name}`).addEventListener("input",()=>{
    $(`#auth-${name}`).removeAttribute("aria-invalid");$(`#auth-${name}-error`).textContent="";
    authFeedback("");$("#toast").hidden=true;
  });
}
$("#toggle-password").onclick=()=>{
  const visible=$("#auth-password").type==="password";
  $("#auth-password").type=visible?"text":"password";
  $("#toggle-password").textContent=t(visible?"hidepassword":"showpassword");
  $("#toggle-password").setAttribute("aria-pressed",String(visible));
};
$("#auth-switch").onclick=()=>openAuth(state.authMode==="login"?"register":"login");
$("#forgot-password").onclick=()=>openAuth("forgot");
$("#account").onclick=()=>{if(!state.session?.user){openAuth("login");return;}busy($("#account"),async()=>{await api("/api/auth/logout",{method:"POST"});await refreshSession();state.results=null;$("#results").replaceChildren();$("#principles").hidden=false;if(state.view==="alerts")loadAlerts();});};
$("#language").onclick=()=>{state.lang=state.lang==="en"?"ar":"en";localStorage.setItem("waypoint-language",state.lang);applyLanguage();};
$("#swap").onclick=()=>{const origin=$("#origin").value;$("#origin").value=$("#destination").value;$("#destination").value=origin;};
$("#interpret").onclick=()=>{if(!requireUser())return;busy($("#interpret"),async()=>{const response=await api("/api/interpret",{method:"POST",body:JSON.stringify({text:$("#trip-text").value})});if(response.query){fillQuery(response.query);toast(t("updatedform"));}else toast(response.clarification);});};
$("#alert-form").onsubmit=event=>{event.preventDefault();busy($("#alert-form button[type=submit]"),async()=>{const response=await api("/api/alerts",{method:"POST",body:JSON.stringify({query:state.results.query,target_price:Number($("#target-price").value)})});$("#alert-dialog").close();toast(response.message);});};
$("#delete-account").onclick=()=>{if(!confirm(t("deleteconfirm")))return;busy($("#delete-account"),async()=>{await api("/api/account",{method:"DELETE"});await refreshSession();state.results=null;$("#results").replaceChildren();$("#principles").hidden=false;toast(t("accountdeleted"));});};
document.querySelectorAll("[data-view]").forEach(button=>button.onclick=()=>showView(button.dataset.view));
document.querySelectorAll("[data-close]").forEach(button=>button.onclick=()=>$(`#${button.dataset.close}`).close());
async function init() {
  applyLanguage();
  try{
    await refreshSession();
    const today=state.session.today;$("#departure").min=today;
    const maxDate=new Date(`${today}T12:00:00Z`);maxDate.setUTCDate(maxDate.getUTCDate()+330);$("#departure").max=maxDate.toISOString().slice(0,10);
    const departure=new Date(`${today}T12:00:00Z`);departure.setUTCDate(departure.getUTCDate()+14);$("#departure").value=departure.toISOString().slice(0,10);
    const params=new URLSearchParams(location.search);const verifyToken=params.get("verify"),resetToken=params.get("reset");
    if(verifyToken||resetToken)history.replaceState(null,"",location.pathname);
    if(verifyToken&&confirm(t("verifyconfirm"))){await api("/api/auth/verify",{method:"POST",body:JSON.stringify({token:verifyToken})});await refreshSession();toast(t("verificationdone"));}
    if(resetToken){state.resetToken=resetToken;openAuth("reset");}
  }catch(error){toast(error.message,true);}
}
init();
