import os
import time
import subprocess
import re
import sys

numberDivisions = 1048576
numberJobs = 8
max_time = 300
sleep = 1
sleepCounter=8
#improve to check for more than only one
#GPL maxConfiguration=77371252455336267181195263
#uClib 
maxConfiguration=14396524142538228424993723224595141948383030778566133225922417832357880258148761185020930195532450742879746914027266864394266451377581759004827248578768524336431103
#BusyBox
#maxConfiguration=9076030935533343889148330677184451660957398691768765008885326289770145612551296225251271450782204288267814476258502032778653474399077793626653018683486295323382390383590453332169716856898789897889643528945016096228440849041002686084943230837088977557446564364344140092918489677823
#uClinuxdis
#maxConfiguration=188501787658138776526316391973679239907820382867140805681144220780050698265428977917842924316820804490882044531700026161400423140624345724347059987430217219443542346615871751089083876220596224387399635909565487009065232689887930358404389913798458461035797425091600762263250923357187307004059038598692050448905404415
#Automotive
#maxConfiguration=4632438043593408345637713970404518697455360929338020700251286164638922833290296261210275471908054082927678172415549545870695145203516810583601635587166351514610107165538745558411647927575883095993165049893845351105218868056451782753236019830913888921058489082707775794350658636371250726835106723373468799969254040720524751617654737817807391884481170174096831879768502222588615092235795245153808394336122063839036464089165027809754697270743823850939537930991563051159465774622775521029734224636204137038372488418330804851673423939219188714502504168696241334506597405937650710750538580209441230455411842593365629840001275402927172252775995877549778214861959632555767771491316538487814557811957312301189020983270233115459583
#uClinuxbase
#maxConfiguration=53011964731314639360170211948944612964704102539734029726489124561294504015911946159546600129546616582963686747580297614112539484367985917450348142164324479806664791755121261307082907400871008789637247661119651509692039792807470747939375057064652404230895696250498153019693037270075500145947185742012497137762341187603993810780342751781066415020030854412546101526061213859287087970134446210330531222307912639519713558202409997545945974290594682478446905781928619834106212867030902653244998157330014042622049124771863130593894113369924880293659151097629295423969359637174269958687311277493322449002501444105518888295419048006500031564348836566009998778068252026426575989164661803420268518371668415529666173159040783223084467238758535589487870699423357464258378641284552952654453813850208224121092383173756478787343283350549338900394576562244966662748241423551249690179956160560366141531351832783336434676173527012791311738766106240195615564804992735124670490648976167391935267318509459583610715725525545793272873249974372976022146124194947837868488697844608115267025917699612067770289012133451821190233555300668713992191
#CDL
#maxConfiguration=13516871715637497063887732875081211731797515874283357168259213682631321993154516266924788625082299793186426895501840727099083391111208685742023711459182410418259906578689061641485944722270168571463607944455747330704677763347287166091616266533224068514610117845814742803945440504029127077401585435194130008559864399385942414166761522880985058682089992528479166503895836786405777454906232787885922917876505134038167429724358515707775538493962844709840424690843624080421550878000647825372064034726416781307161191635809449099239777274674016684689029661050726356149834034067471463716707288645682965071433495673536787630579334728911372883171048071542538035978821562537518343816247969955644223008693198901850707966405958116990330218515810313997132201969217226629713550807065022929562180223813940101173388506548148613128866602425315419846215887040585708487637675270771660605371869582355246095243580882722349570269485735336314462744830780129786567255263455594852911190382600387684056949348772531984585901409930158136400043715381876168707326078312277445987957826037930313387104114389019383839405626450213259566343333718509596020861851762225197678442407900583607525909309512157937950119809527830884520781044946929882944198459693621001738217297781001276150872730351466729189385616436446063678072767102754705925775045004647995319727223037657735165197862095355037676316580085619120472733368936728672555196942603793771651129510018832321152528255038579061077191032812298386678555521811020005896386129836943424380742701118224294990030702771673688535564907759879935377985742667470308019368038712785886723043885363442982887997658254889055289263263693144786076243126576322607016990770766869707739254723565119641134696983187744874330794234556016698362571068763692421660671853575005989413005959219475944641027627099598885084328523180210995863524459722848826382705907732214429586414070342179046666822849907227135566072323714340769766503391918674127035922476981957478019419463332900611605182503000322258496177756280089496255200326896112310189212501625184123978562368611906038105339858229445062380317203864495535520323016615862925764295856953760685846035482528253607069750548354253219108401599539483401924922120922351264118491944015978470733100827495665898274903435995475517880433395661727694846497634283558986176847339127826290969199879645126172140607233245534709111324671
#EMB
#maxConfiguration=27758328010108391723533273051008521401993215107035853860962271509829959414991954804542791240949187357328752676867337961924993821362274829464380491878691646967929615139973395103485454182165082507767865352204915092169831515773096229763635230504341452127768395580288695779220769180396125392108681192985899867405199975492259156166400087675352193807266815825825559626237976357232530819808849431186185533093730210220413530721834200367359590112943266769312065293137780211892341872263947510247481033349428117271090825986173130524037354786306369305869408398495296608372756447787337467749685600444007484121293658444761556356564545046525035036071050093340975855951062119562076586150797616658314014567300155037618253111163246560690095300395918268372881910776040517966002539873659423871745071151990002361010180747332120023040721618561270671273476093299695273757453223165320773225092224201247850584664724834134620199070306164863568320056586319767627757948448536988617791506995943598638701413265107555475735991733776767779392976305002642866794971653166455103099733018686600742668982378084739529367886729769425393945575321083644863283089237459071120195423323017913434314290581358619417250681568965896058756282479411076584225368964158205479888764961933104547766491268413600426220682383711677026228323838237476148149349680222621907436150991689694135653693550625992493810103309030557880242193639924953674542944066028649652271837066798192426291756254908789287345488574265594044050499851092442601937988214490950960105932088997180421193364407518702477368152584155818298871177696138918564942688353406567469847763116772006564825546284892467533865601911053323432620537965338194539029004494933893486957531544952355223090459423067328760082811289256284758211692064632217446033785797534513446639571994716915827358250581798438358528420761750894859752675742298044006325487838050473717796580039221590350871431482773833912751664908636861370075690538572606235338282010973642525454144079785700794930652557153460112867552223697456421389395401123569186361815919325920802540086945090977911438741680089253055217217177586247174285181755888111260913591296864045319999773937058270216040005249683366273812514900862705896654303222572030018103878017596507010174083910738765277253969517371148583393313686689265006552517600478301962414464264920295420329679270914949911516866010620953170204464123011235261568386232401056832786351823212441770177134573959190358833337476948307247706332301597398781825876154153769225709660278230200846751139814792381966092726070784224094297117456070252778617145706709656440283145113498155614515535257399680499877182193616256928251090675390652170791826103786209370816456035921247627956223599019860400533736763328079990159578818662209991261429016456244712459394863471229626488236998886551196354312183876613453864822058974999540443946521840759594444372659710560683266155893422245718528743886109873064799576952909037403109951379442433381433561370702064229529609491509566823049145451299333586238842719521865024147743213391181036305508894890186043154572567836715572567684322520364874271456174115102060043602307575481542742765107580923131747073939802199161614871683045959799889824545549476940706269525100058767356030540705256245066066915188585357872463991610633217178147141783701857377055001773334478698027504696042635803828792200423359706080069854272385603573838103026351649278991449129203534757812890471461633035687121089822007080680178066060234751636945325091147850519208419901082318524429104222562384292913286826267971033539009803318896538999450837083752457173289263869148117280044231489374948981104136804589813118285611631108433791321782113062816155316217858296509271522444335420257993545604365263956453384438796804007063433604759940038446085010563851333443975661788404100869927238829773481532600550689135743482808051952368967087256667636793152012202684326884130970025651931094543188544370319506918109692321093851277999599216902418616990761656913782966564423506092362415176618118289087518469419984572942222367493845449539395667882299161207861023359581482675355944802933526649438708249277336577825692759878297079901588411843935874861824516136163481663760928610430330676024409427205107662132634330724277867011929935735975482492828013977008777838157288046283818594001169866994383329844639554862371757718654371461612524242880298127899157861986091585066147643953769942723087841697882567163240208126166147316455549871035181070758334646023831829048367672624556281644410406216029646588683729926830166295564208865451881921592964495380884233373048398590432462848478513035356202962139910889533482041534562609938395983864710055604728369031603453848762806335176703
#Linux
#maxConfiguration=35491429886508894331195444165643421936400272236224441038750707304395956802707937942206117316302597458682490763519563555728649187723522567117779218060386909082886777786324264848968774065626535597563803893501221477456023096440472732053693198547503554933237465316451200315410255366685879857561989294092634321016899990159102803751935772274680973594030753406084150808866265189254320342497496596685612920509524950670055920888819476244955064920959801852442459377409476183647190639988140273495060317939002956507163553355024576591208107068150823972473871139769493982712887864966751578626121188195707589402250744916886960737317242337993887377265630951010660797540716202841858803713890770627608748846854277464300307676501787872325765290442617944842857417068106632564601185907706921311214824779638315558073158981348864072292746676401778955425070683160692916998352456975391023223197119850544895966129960281952320465274045685282315633356452570857875611479927498985891306679152947990757052699251581408166940360900922507005501797103130055205318517181787216760484087203060994972555846335318371457201301289257678561121588692153841224858766684940041447307711595276448086762099230599354279516751399147851361528411961752058323389317466304475981584897917792062359396967332810090417902693473766714674887785672161761254468811919725014195258899952449258971382530522948548309967717108009291708400070861389781558977911551598023211207889402997006155473546705687013225264116001010210024930488282266748148885076229870892564355609146726753221836734107032930014433868286333340439677280410830142657963562155622659133713885314122640880733046778880200161347194458307326406687271713647218349459706858504048871027602073193476857627440367167901762858187581370512269177275538510258696710733647667970536799845216510787593585109428299444302572105769453185899163429165068910667039555951737283954063460511873063552317811611889226172302432588977104815690682662823828403977570655552299713120110596183666717619787311460778909159851136372177552724439734985487206862194449177369370358837259980406672313205129051899075494773667647259955559025995617810883779397725380012446737348273299332492665247651226117231369629305539322913742044350995076932081988923654535256708103306450578843552570408505654809365221027196114052816280769977364070009264255460457330263100079524208221095755155111289809648398934169184037648533431375099429844633213878147362459561106826317502685180464638034845770114640079425373217218552192710052216113189884064850518587625290892083256460706125815523282903899798407658008298906912066128799074225493429209167972584653444589683877038122695669598826059154554343360183797566040485845765834462596742914626067503694994655186589458465251487517781833445542190987033782906752038076192718939992886145363540350868938897494128425899981399957843641420195038609729293995579154024219614495661227270996477789789548792027972000625461460019982226518464444319244214974701205413773595543594244162331585596731447681127585096978325275814541017345675942846028998471553633594597938619933098950926283743413858165648558039527853234509747577102276949381482943370415032944971686869385574729387303421018283526992984002573276479538935787982227706325945988213751766124215573091244751912790935923937394704127787590749893139888573968567692422486581183806039408986779263944315349029152814939142326589742871346791181183137673680167190863216058337891373476866195514781678034128716920644174057362359956464331056941815502548027505985089925473003281997470437868884030625664462254740974297845476376455409809666676629334676483135364336913807428432938981335991128442640829244001648922384132391317221144613204687830942759612492305897584067785263371276899906585669222815123218295826187796608074404207419496607682926681522189972581525841386490964556940048085127212041037324033637279567777806787061659546097434955428677367070005156563437890433511267811122182510687812771021650274851931043762085597213804633557073889402466891005383782111065961543422297390391924850115040126898829975107669445190069697955634645219831359283606752319385816326178345278578875363840468207721884820625357540861693043797797734162586500502153930208459113930471413931001367795729794665570063213759172503844254465827862215308039721885961974959366676097775585429555773618684770388019180067970071625907497414810436852180712272225254090501692193201002569158086028699903142160840477289769149064184002598225408111816255955253362696314216772566001720933096454399108242243728638925450528265836768289403625778075047731320321124810074092131562474870190042129551527341524944468336586036907822746872356321583965140580905504196323213052718204685811297173093518775845796648837016003852632213291641866381370210237746443477187045702952325118733275508100941258344308940883686407971272159623195842741048544143501183663126088799942501130834136144812800855347723154587530137221484193370563377782827893469607719538273385595308851146405876913486945914499138930483790618928716615069320212782916571765373091858122051992641701644324968667746206809105023960342886271277938263917361337138764319117854930905522577711650396574771430344121799043246820985311768177278823446346446836198854485107583028400456540062611973363318555695905529186713508684667784456484179961958713270525848128827630234098743812504720525690672964133854785610946598936635175363531496783747860306995911523038958268044452050684591653094386872947336576667184193437320669970508411125705500648597641617315890879157421055304982229643892321080511211665769487960144981712661461696460872934992306531895995886841243734141795276461007230884066637012635843279347599595028342047251829618554588881916143479329193565404541531296807827140425893143629757976473121763232317802699914012416255935733460629283905259144298701890706879908606289318602403492936739177166174206310008566579060685129754160093774037174109937239060275086236666185410067896284585407777954142353934717368003561300005062298796398541682937396844983382266790164425906890727256624330500585495702096240330890882538616406023737206617416227726010713022826566306064608417496611603138295209997919396731530047573482352152066804134707888406114968243737674198359175362637584580701156210460004926683763530602103905752616536354992069943145007823696322023314014700723986962177183798057283104667110212749952140900506768354621746609084991204106997009346505038116775074234553443028395649101525194987220810761956031533089582180427117992654993104068654848589781617484866041272875005303199658809127911142757354403437971399058004554044830413043177708748571682176078809784603487080248030005657405202852903426988423693360811934801514735913656593912498217060085664129456234383246676537922075637882230504043699633265764008221651989657404903328840915043169897994092982526411248142657070994154394066360079539461601405089548458112004215135598679074323418280193680534923405851213876198849649544204880776310426382076823926601279729750992248687474289814533074354816080692962839294094485110083070765490044545286540227427184612498528214653150182525961428460224822728315889290641785247986842511555521611291763014879252572338866815260903195891283908991362212267516353399755334113288416530298993938250275214301386351078457985979342959711026894240046365022865055217886978248978026235075949572640493697644058319077003298221037815342335266858248865415618432332888142798597377020907316456817945025341999084443712161810841817951788469052075442835524612267015035412954937648121114554209327980470721971740211033060067569330123820498938280454424457407239144724199014192052517674752638945535205899267599450214987902983494735781945910636219300376681186217727641416140983334480594190649836664883781842229679756730810780124488224727566829816286292447153922002840793544467028766867533458043653678665547711623296844040461404181856720932020989427757829003280671284343444392037981134868127640478854235499160483771964790151137536138281281920928175444460553283329870836504777556134266006094221066679050738679378891688973041370668259006377136241302615695996682092756532470880130023749367338225677378898095734813850585644918356892123737587747868280166074274045708235906530797641239299807788776714475989912578908774598567791291244359537358430682590713813017718897063366960003254056433708410850855576134712644749492340755863761146139828385282605486023700331396859724387361133119794344334399508875181406265839044955062161212249450312171282680259876322917207558129782918750549528295371858534952030826253032654983725055870283618738020207059739024460544064190018083727515603104020068081172300841747587391527336805547793593133930225382805584910806106507312452709065529351587689360445453837489094162429577917743436836165968292800945390344407923179895624360758223177803669936184806003182604160901240468560400013144666262760349805967080957402025869455621357567



#maxConfiguration=77371252455336267181195263



model="fm_models/simples/uClibc_simple.uvl"
#model="fm_models/simples/Krieter2020o_simple.uvl"


cont = 0 

for i in range(numberJobs):
        fS= "./OutputR_1_" + str(i) + "-" + str(numberDivisions) + ".err"
        comando= "/usr/bin/time -o " + fS  + " python ./../picassofiles01main.py ./../" + model + " " + str(numberDivisions) + " " + str(i) + " " + str(numberJobs ) + " " + str(max_time) + " &"

        #comando= "/usr/bin/time -o " + fS  + " -f \"%U %S\" python ./../picasso01main.py ./../" + model + "  " + str(numberTasks) + " " + str(i) + ficheroCSV + str(min_time) + " " + str(max_time) + " &"
        #print(comando)
        os.system(comando) 
    
        cont+=1
        if (cont>sleepCounter):
                cont=0
                time.sleep(sleep)

   