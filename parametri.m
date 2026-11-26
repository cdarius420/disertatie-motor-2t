function P = parametri()
% PARAMETRI  Parametrii de lucru ai conceptului, într-un singur loc.
% Toate scripturile citesc de aici. Valorile marcate [ESTIMARE] sunt ținte
% sau presupuneri de lucru, de înlocuit cu datele motorului de referință.
%
% Decizii (23.11.2026):
%   cotele de bază 54 x 54,5 mm rămân; injecția în ferestrele de transfer (TPI,
%   2 injectoare); pornire cu decompresor + rotire înapoi; controler 380 A;
%   limitator la 10.500 rot/min; lucrarea e numai simulare (fără motor de validare).

% --- Motor 2T, 125 cm3 ---
P.B      = 0.054;    % alezaj [m]                              [ESTIMARE]
P.S      = 0.0545;   % cursă [m]                               [ESTIMARE]
P.L      = 0.110;    % lungimea bielei, între axe [m]          [ESTIMARE]
P.r      = P.S/2;    % raza manivelei [m]
P.Ap     = pi*P.B^2/4;   % aria pistonului [m2]
P.Vd     = P.Ap*P.S;     % cilindreea [m3]
P.CRt    = 7.5;      % raport de compresie reținut, de la închiderea evacuării [ESTIMARE]
P.thEO_deschis = 82; % deschiderea evacuării, supapa deschisă [grade după PMI] [ESTIMARE]
P.thEO_inchis  = 92; % deschiderea evacuării, supapa închisă [grade după PMI]  [ESTIMARE]
P.thTO   = 116;      % deschiderea transferului [grade după PMI]             [ESTIMARE]
P.thIGN  = 345;      % aprinderea: 15 grade înainte de PMI                   [ESTIMARE]
P.w_ev   = 0.038;    % lățimea efectivă a ferestrei de evacuare [m]          [ESTIMARE]
P.w_tr   = 0.040;    % lățimea efectivă totală a ferestrelor de transfer [m] [ESTIMARE]
% Așezarea transferurilor (Schnürle cu boost): A principale ±, B secundare ±, C boost
% în spate, opus evacuării. Unghiul centrului de la axa evacuării; suma lățimilor = w_tr.
% Boost-ul se alimentează pe canal propriu de la compresor: pistonul n-are ferestre,
% fiindcă raclorul ține uleiul din carter sub ferestre.
P.tr_unghi  = [62 105 180];        % [grade]                                 [ESTIMARE]
P.tr_latime = [9 6 10]*1e-3;       % coarda fiecărei ferestre A, B, C [m]    [ESTIMARE]
P.punte_min = 3e-3;                % puntea minimă dintre ferestre, la alezaj [m] [ESTIMARE]
P.unghi_stift = 140;               % știfturile segmenților, pe peretele plin [grade] [ESTIMARE]
P.m_rec  = 0.255;    % masa alternativă măsurată în Fusion: piston, bolț, siguranțe, segmenți, rulmentul piciorului, partea alternativă a bielei [kg] (s12, B5)
P.p_cc   = 0.5e5;    % presiunea în carter la PMI, unde forțele sunt maxime [Pa]: lamela îl ține sub
                     % presiunea băilor; s14 (U3) verifică că presiunea reală nu coboară sub ea (acoperitor)
P.p_ev   = 1.0e5;    % presiunea medie la evacuare după destindere [Pa]
P.gamma  = 1.32;     % exponentul adiabatic în cilindru

% --- Piston și segmenți ---
P.imep_plin = 7.0e5;  % PMI la sarcină plină: 11 kW la 9.500 rot/min + frecare [Pa] [ESTIMARE]
P.f_proiect = 1.3;    % factor peste presiunea maximă calculată (avans, detonație) [-] [ESTIMARE]
P.seg_n_comp = 2;     % segmenți de compresie, cu știfturi de poziționare
P.seg_t   = 2.2e-3;   % grosimea radială a segmentului [m]                 [ESTIMARE]
P.seg_h   = [0.8e-3 1.0e-3 1.5e-3];  % înălțimi axiale comparate [m]
P.seg_E   = 150e9;    % modulul de elasticitate, fontă nodulară [Pa]        [ESTIMARE]
P.seg_rho = 7200;     % densitatea segmentului [kg/m3]
P.seg_pe  = 0.15e6;   % presiunea elastică țintă pe cilindru [Pa]           [ESTIMARE]
P.CS_seg  = 1.5;      % coeficientul de siguranță cerut materialului segmentului
P.h_comp  = 0.027;    % înălțimea de compresie: coroană -> axa bolțului [m] [ESTIMARE]
P.joc_raclor = 0.002; % raclorul rămâne cu atât sub ferestre la PMI [m]     [ESTIMARE]
P.zona_raclor = 0.0035; % înălțimea zonei raclorului pe fustă [m]           [ESTIMARE]
P.joc_cg  = 0.003;    % jocul dintre fustă și contragreutăți la PME [m]     [ESTIMARE]

% --- Cilindrul și ajustajul piston-cilindru (s08; pasul 2 din Fusion) ---
% Reper: Yamaha YZ125, tot 54 x 54,5 mm: alezaj 54,000-54,014 în 4 clase,
% piston sortat pe clasă, joc 0,040-0,045 mm (manualul de service).
P.t_perete   = 0.006;     % peretele cămășii [m]                          [ESTIMARE]
P.deck       = 0.0;       % puntea cilindrului deasupra coroanei la PMI [m] [ESTIMARE]
P.alezaj_tol = 14e-6;     % alezaj Ø54 +0/+0,014 [m]
P.n_clase    = 4;         % clase de sortare alezaj/piston
P.joc_piston = [40 45]*1e-6;  % jocul la rece pe perechea sortată [m]
P.alfa_cil   = 22e-6;     % dilatarea cămășii, aliaj de Al cu Nikasil [1/K] [ESTIMARE]
P.alfa_pist  = 19.5e-6;   % dilatarea pistonului forjat Al-Si [1/K]          [ESTIMARE]
P.T_ref = 20; P.T_cil = 130; P.T_fusta = 150;  % la sarcină plină [grade C]  [ESTIMARE]
P.joc_cald_min = 10e-6;   % jocul minim la cald, pentru filmul de ulei [m]   [ESTIMARE]

% --- Pistonul și bolțul (s09; pasul 3 din Fusion), pe baza pistonului YZ125 ---
% YZ125: piston 53,957-53,972 măsurat la 17,5 mm de marginea fustei, bolț
% 14,995-15,000 mm, segment unic 1,0 x 2,35 mm. Kitul Wiseco: bolț 15 x 41 mm,
% rulment de picior 15 x 19 x 17,3 mm, piston forjat din 4032.
% Diferențe față de YZ125: doi segmenți de 0,8 mm cu știfturi (s06) și raclor jos
% pe fustă; fusta e mai lungă și fără ferestre (boost-ul are canal propriu).
P.seg_h_ales = [0.8e-3 0.8e-3];  % înălțimea celor doi segmenți de compresie [m] (s06)
P.cap_sus    = 3.0e-3;   % coroana -> primul canal (top land) [m]          [ESTIMARE]
P.punte_seg  = 3.0e-3;   % puntea dintre canalele segmenților [m]          [ESTIMARE]
P.joc_lat_seg = 0.04e-3; % jocul axial al segmentului în canal [m]         [ESTIMARE]
P.joc_rad_seg = 0.15e-3; % jocul radial la fundul canalului [m]            [ESTIMARE]
P.rac_h = 2.0e-3; P.rac_t = 2.2e-3;   % raclorul în trei piese, B x T [m]  [ESTIMARE]
P.t_coroana = 5.0e-3;    % grosimea coroanei [m]                           [ESTIMARE]
P.t_fusta_p = 2.5e-3;    % grosimea peretelui fustei [m]                   [ESTIMARE]
P.perete_canal = 2.0e-3; % peretele rămas în spatele fiecărui canal [m]   [ESTIMARE]
P.d_bosaj   = 25e-3;     % diametrul exterior al bosajelor bolțului [m]    [ESTIMARE]
P.d_bolt    = 15e-3;     % bolțul, ca la YZ125 (14,995-15,000) [m]
P.d_bolt_int = 9e-3;     % alezajul bolțului tubular [m]                   [ESTIMARE]
P.l_bolt    = 41e-3;     % lungimea bolțului (Wiseco S467, 15 x 41) [m]
P.b_picior  = 15.9e-3;   % lățimea piciorului bielei, YZ125 din 2022 (biela de 110 mm) [m]
P.joc_ax_biela = 0.5e-3; % jocul axial al piciorului bielei, pe fiecare parte [m] [ESTIMARE]
P.bolt_tol  = [2 13]*1e-6;  % alezajul bolțului în piston: 15,002-15,013 [m] [ESTIMARE]
P.Re_bolt   = 600e6;     % limita de curgere a miezului bolțului cementat [Pa] [ESTIMARE]
P.CS_bolt   = 2.0;       % coeficientul de siguranță cerut la încovoiere [-]
P.p_bosaj_adm = 60e6;    % presiunea admisă în bosajele de aluminiu forjat [Pa] [ESTIMARE]
P.piston_YZ125 = [53.957 53.972]*1e-3;  % plaja pistoanelor YZ125, pe clase [m]

% --- Biela și arborele cotit (s10; pașii 4-5 din Fusion), după YZ125 ---
% Biela YZ125 din 2022: 110 mm între axe, cap Ø28 și picior Ø19, late de 15,9 mm.
% Manetonul Ø22 x 54,5 mm cu șaibe de 1 mm (kiturile de bielă YZ125).
% Ambielajul YZ125: lățime 55,90-55,95 mm, bătaie max. 0,03 mm.
% Rulmenții paliere YZ125: 63/22 (22 x 56 x 16), Cr = 20,2 kN, C0r = 9,25 kN [catalog] (NSK E1103, partea C; bom/piese_cumparate.csv).
P.d_maneton = 22e-3;  P.l_maneton = 54.5e-3;
P.D_cap = 28e-3;  P.D_picior = 19e-3;    % alezajele bielei (rulmenți cu ace) [m]
P.D_ochi_cap = 36e-3; P.D_ochi_picior = 24e-3;  % exteriorul ochiurilor: pereți de 4 și 2,5 mm [m] [ESTIMARE]
% Tija în I (buzunare pe ambele fețe): lățimea la centrul ochiurilor, tălpile laterale,
% inima din mijloc, racordarea tijei cu ochiurile. Masa iese ca la o bielă YZ125.
P.tija_lat = [16 11]*1e-3;   % lățimea tijei la cap și la picior [m]       [ESTIMARE]
P.tija_talpa = 2.5e-3;       % talpa laterală a profilului în I [m]        [ESTIMARE]
P.tija_inima = 3.0e-3;       % inima profilului în I [m]                   [ESTIMARE]
P.racord_biela = 6e-3;       % raza racordării tijei cu ochiurile [m]      [ESTIMARE]
P.Re_biela = 785e6;          % limita de curgere, oțel de bielă (SCM435 călit) [Pa] [ESTIMARE]
P.saiba = 1.0e-3;  P.joc_lat_cap = 0.35e-3;     % șaibe; jocul lateral al capului [m]
P.D_saiba = 32e-3;                              % exteriorul șaibelor [m]   [ESTIMARE]
P.latime_amb = 55.925e-3;  P.bataie_max = 0.03e-3;   % ambielajul, ca la YZ125 [m]
P.d_fus = 22e-3;  P.rul = [22 56 16]*1e-3;  P.rul_C = 20.2e3;  P.rul_C0 = 9.25e3;
P.joc_rulment = 0.5e-3;          % de la braț la rulment [m]                 [ESTIMARE]
P.capete = [46.5 44]*1e-3;       % capetele arborelui, de la rulment: stânga (+Y) variatorul (+6,5 mm pentru gerotor, MR-018), dreapta (-Y) mașina electrică [m] [ESTIMARE]
% Mașina electrică stă pe dreapta, în locul aprinderii; rotorul se prinde clasic, ca la YZ125:
% con 1:5, pană Woodruff (doar poziționează, cuplul îl ține frecarea pe con) și piuliță M12 x 1,25.
P.joc_con = 2e-3;                % de la simering la începutul conului [m]          [ESTIMARE]
P.con = [20 20]*1e-3;            % conul rotorului: diametrul mare, lungimea [m] [ESTIMARE]
P.conicitate = 5;                % conul 1:5 pe diametru (conul clasic de volant magnetic) [-]
P.d_filet = 12e-3;               % filetul piuliței rotorului M12 x 1,25 [m]
P.pana = [3 5 13 3.8]*1e-3;      % pana Woodruff DIN 6888 3 x 5: b, h, D, adâncimea în arbore t1 [m]
P.M_piulita = 50;                % strângerea piuliței rotorului [N m] (YZ125: 40-55)
P.K_piulita = 0.2;  P.mu_con = 0.15;   % coeficientul de strângere; frecarea oțel-oțel pe con [-] [ESTIMARE]
P.CS_con = 3;                    % siguranța cerută la alunecarea rotorului pe con [-]
P.L10h_min = 2000;               % durata L10 cerută la mers prin oraș [h]   [ESTIMARE]

% --- Echilibrarea (s12; brațele din pasul 5) ---
% Carterul nu baleiază (compresor), deci brațele nu trebuie să fie discuri pline ca la
% YZ125: sector de contragreutate + bosajul manetonului, legate prin tangente.
% Masele pieselor mobile vin din Fusion (volum x densitate), vezi echilibrare.m.
P.BF = 0.55;                     % factorul de echilibrare [-]: cu masele din Fusion maximul e 0,61, deci 0,55 lasă rezervă
P.R_bosaj = 18e-3;               % bosajul manetonului în braț: perete de 7 mm [m] [ESTIMARE]
P.perete_fus = 5e-3;             % brațul minim în jurul fusului palier [m]  [ESTIMARE]
P.rho_piston = 2680;             % aliajul pistonului forjat (4032) [kg/m3]

% --- Carterul (s14; pasul 9 din Fusion) ---
% Două semicartere, împărțite pe planul cilindrului (Y = 0), ca la YZ125. Baia de ulei e în
% carter (ungere ca la 4T, baleiaj cu compresor), deci carterul stă la temperatura uleiului.
% Rulmenții paliere stau în bucșe de oțel turnate în aluminiu: presați direct în aluminiu
% (ca la YZ125, unde amestecul proaspăt răcește carterul), la 90 °C și-ar pierde strângerea (s14).
P.joc_carter = 3e-3;          % jocul radial brațe-carter [m] (ca la fustă)        [ESTIMARE]
P.joc_carter_lat = 2.5e-3;    % jocul brațe-perete, în afara bosajului rulmentului [m] [ESTIMARE]
P.t_carter = 5e-3;            % peretele carterului turnat (AlSi9Cu3) [m]          [ESTIMARE]
P.t_bucsa = 4e-3;             % peretele bucșei de oțel a rulmentului [m]          [ESTIMARE]
P.perete_bosaj_rul = 8e-3;    % aluminiul din jurul bucșei [m]                     [ESTIMARE]
P.simering = [22 35 7]*1e-3;  % simeringul de pe fus, d x D x B [m]
P.joc_simering = 1e-3;        % de la rulment la simering [m]                      [ESTIMARE]
P.baza_cil = 62e-3;           % planul bazei cilindrului, de la axa arborelui [m]  [ESTIMARE]
P.joc_gura = 0.25e-3;         % jocul radial al cămășii în gura carterului [m]     [ESTIMARE]
P.gat_lat = 100e-3;           % lățimea gâtului carterului, sub baza cilindrului [m] [ESTIMARE]
P.joc_fanta = 2e-3;           % fanta bielei spre gura cilindrului: alezaj + 2 x 2 mm [m] [ESTIMARE]
P.prezon = [8 6.8 18]*1e-3;   % prezoanele bazei: M8, burghiu 6,8, gaura de 18 mm [m]
P.prezon_raza = 48e-3;        % raza prezoanelor față de axa cilindrului [m]       [ESTIMARE]
P.prezon_unghi = 40;          % ±40 și ±140 grade de la evacuare: între ferestre [grade]
P.perete_min = 3e-3;          % peretele minim de aluminiu lângă găuri [m]         [ESTIMARE]
% Ungerea: ca la 4T, dar cu cavitatea arborelui uscată. Pistonul pompează carterul: la coborâre
% împinge prin lamela din spatele-josul cavității uleiul scurs din rulmenți (și gazele scăpate pe
% lângă segmenți) în băi; la urcare lamela se închide, deci uleiul nu se mai întoarce la arbore.
% Băile stau în fața și în spatele arborelui, urcă până la axa lui și nu coboară sub rotorul
% mașinii electrice. Sunt unite pe sub cavitate: un tub în U, cu sorbul pompei la mijloc, unde
% nivelul nu se mișcă la frânare și accelerare. Pe lateral au aripioare de răcire, în spațiul
% dintre baie și fața carterului; înăuntru, câte o șicană care frânează valul.
P.V_ulei = 0.30e-3;           % uleiul [m3]: doar rulmenții și cilindrul (fără cutie de viteze, fără distribuție) [ESTIMARE]
P.rho_ulei = 870;             % densitatea uleiului [kg/m3]
P.baie_x = 120e-3;            % capetele băilor, în față și în spate, de la axa cilindrului [m] [ESTIMARE]
P.tesire = [20 25]*1e-3;      % teșiturile exterioare: jos (lovituri, garda la sol), sus [m] [ESTIMARE]
P.sicana = [3 6]*1e-3;        % șicana din mijlocul fiecărei băi: grosime, fanta de sus și de jos [m] [ESTIMARE]
P.aripioare = [3 8]*1e-3;     % aripioarele de răcire: grosime, pas [m]            [ESTIMARE]
P.joc_capac = 2e-3;           % vârful aripioarelor sub fața carterului (capacele) [m] [ESTIMARE]
P.unghi_lamela = 235;         % fereastra lamelei pe cavitate, de la +X spre +Z: spate-jos [grade]
                              % (arborele se rotește înainte, ca roata: jos, uleiul e dus spre spate)
P.fereastra = [30 12]*1e-3;   % fereastra lamelei: lățime (în lungul arborelui) x înălțime [m] [ESTIMARE]
P.sa_lamela = 3e-3;           % sediul plan al lamelei, peste peretele cavității [m] [ESTIMARE]
P.t_lamela = 0.2e-3;          % lamela, oțel de arc [m]                            [ESTIMARE]
P.n_carter = 1.4;             % comprimarea aerului din carter: adiabată (acoperitor)
P.a_frana = 1.0;  P.a_accel = 0.4;   % decelerația la frânare și accelerația, în g [ESTIMARE]
P.sorb_min = 10e-3;           % sorbul rămâne acoperit cu cel puțin atât [m]       [ESTIMARE]
P.aer_racire = [50/3.6 70];   % viteza aerului [m/s] și diferența ulei-aer [K] pentru estimarea răcirii
P.k_al = 110;                 % conductivitatea AlSi9Cu3 [W/m K]
% Ajustajele rulmenților 63/22 (SKF: inel interior cu sarcină rotitoare -> strâns pe fus;
% direcția sarcinii pe inelul exterior nedeterminată -> M7 în carcasă), joc radial C4.
P.T_carter = 90;  P.alfa_carter = 21e-6;  P.alfa_otel = 11.5e-6;    % [grade C], [1/K]
P.tol_rul_D = [-13 0]*1e-6;   % inelul exterior Ø56, clasa normală (ISO 492) [m]
P.tol_rul_d = [-10 0]*1e-6;   % alezajul inelului interior Ø22 [m]
P.tol_bucsa = [-30 0]*1e-6;   % alezajul bucșei Ø56 M7 [m]
P.tol_fus   = [2 11]*1e-6;    % fusul Ø22 k5 [m]
P.tol_S7_al = [-72 -42]*1e-6; % referința fără bucșă: Ø56 S7 direct în aluminiu [m]
P.joc_C4 = [20 36]*1e-6;      % jocul radial C4 al rulmenților, alezaj 18-24 mm (ISO 5753) [m]
P.k_inel = [0.8 0.7];         % cât din strângere trece în joc: inel interior, exterior [-] [ESTIMARE]
P.dT_inele = 10;              % inelul interior mai cald decât cel exterior [K]   [ESTIMARE]

% --- Chiulasa și squish-ul (s11; pasul 6 din Fusion) ---
% YZ125 de serie: squish ~1,1 mm măsurat; reglat la 0,7-0,76 mm doar cu benzină de concurs.
% Blair: viteza maximă de squish de 15-20 m/s la turația de putere.
P.SAR = 0.45;              % aria benzii de squish / aria alezajului [-]    [ESTIMARE]
P.x_sq = 1.1e-3;           % jocul de squish la PMI [m]
P.MSV_max = 20;            % viteza maximă de squish admisă [m/s] (Blair)
P.H_chiulasa = 30e-3;      % grosimea chiulasei, cu cămașa de apă [m]        [ESTIMARE]
P.d_bujie = 12.8e-3;       % alezajul bujiei M14 x 1,25 (burghiu) [m]
P.sig_d = 1.0e-3;          % siguranțele bolțului, sârmă rotundă (Wiseco CW15) [m] [ESTIMARE]

% --- Ardere (funcția Wiebe) ---
P.wiebe_a = 5; P.wiebe_m = 2; P.wiebe_durata = 55;   % [-], [-], [grade] [ESTIMARE]

% --- Compresorul electric și admisia (s16; pașii 12-13 din Fusion) ---
% Baleiajul îl face un compresor centrifugal cu motor propriu de mare turație, pe 48 V. Nu stă pe
% arbore: la 10.500 rot/min, o roată cu viteza periferică de 250 m/s ar avea 450 mm. Energia vine tot
% de la mașina electrică de pe arbore, prin baterie. Turația compresorului dozează aerul, deci el ține
% loc și de clapetă de accelerație. Aerul trece întâi peste motorul compresorului (îl răcește), apoi
% prin roată și spirală, într-o galerie inelară din corpul cilindrului, sub ferestre, și urcă prin
% cele cinci canale de transfer. Benzina se injectează direct în cilindru (injector în chiulasă), după închiderea ferestrelor.
P.eta_i = 0.30;      % randamentul indicat la sarcină plină [-]              [ESTIMARE]
P.AFR = 13;          % amestecul la putere maximă, puțin bogat [-]           [ESTIMARE]
P.LHV = 43e6;        % puterea calorifică a benzinei [J/kg]
P.h_vap = 350e3;     % căldura de vaporizare a benzinei [J/kg]
P.TE = 0.65;         % randamentul de reținere: baleiaj în buclă, cu tobă de rezonanță [-] [ESTIMARE]
P.Cd_tr = 0.65;      % coeficientul de debit al ferestrelor de transfer [-]  [ESTIMARE]
P.T0 = 293;  P.p0 = 1e5;   % aerul din jur [K], [Pa]
P.dp_filtru = 0.02;  % pierderea relativă de presiune în filtru și pe lângă motor [-] [ESTIMARE]
P.PR_max = 1.6;      % o treaptă, fără răcitor intermediar [-]
P.roots = [12000 0.80 0.55 0.40 1.5];  % Roots proiectat (MR-003): turația rotoarelor [rot/min], randamentul volumetric,
                     % randamentul izentropic, V_rot/(D^2 L), L/D [-] [ESTIMARE]
P.n_roots_max = 18000;  % turația maximă de lucru a unui Roots mic de serie (Eaton TVS R410, eaton.com) [rot/min]
P.k_plin_roots = 0.6;   % cât din cilindrul D x L al unui rotor e metal [-] [ESTIMARE]
P.eta_c = 0.70;      % roata centrifugală veche: doar pentru colectorul existent, până la MR-008 [-] [ESTIMARE]
P.psi_c = 0.70;      % coeficientul de lucru al roții cu palete înclinate înapoi [-] [ESTIMARE]
P.n_comp = 110000;   % turația compresorului la putere [rot/min]            [ESTIMARE]
P.roata = [0.70 0.30 0.08 0.35];   % roata: D1/D2, butuc/D1, b2/D2, lungimea axială/D2 [-] [ESTIMARE]
P.u2_max = 400;      % viteza periferică admisă, roată frezată din aluminiu forjat [m/s] [ESTIMARE]
P.d_ax_c = 8e-3;     % arborele compresorului, la rulmenții hibrizi cu bile ceramice [m] [ESTIMARE]
P.DN_max = 1.2e6;    % rulmenți hibrizi unși cu vaselină [mm rot/min]
P.eta_em_c = 0.90;   % motorul și invertorul compresorului [-]               [ESTIMARE]
P.sigma_c = 10e3;    % forfecarea în întrefierul motorului răcit cu aer [Pa] [ESTIMARE]
P.Lr_c = 3;          % lungimea rotorului motorului / raza lui [-]           [ESTIMARE]
P.k_supra_c = 3;     % cuplul de vârf al motorului compresorului / cel nominal [-] [ESTIMARE]
P.k_plin_roata = 0.5;  % cât din anvelopa roții e metal (butuc și palete) [-] [ESTIMARE]
P.t_pornire_max = 0.25;  % până la turația de putere: cât compresoarele electrice de 48 V din serie [s]
P.J_cont = 6e6;      % densitatea de curent continuă a mașinii de pe arbore [A/m2] [ESTIMARE]
P.D_motor_c = [50 60]*1e-3;   % carcasa motorului compresorului: diametru, lungime [m] [ESTIMARE]
P.t_carcasa_c = 3e-3;  % peretele spiralei [m]                              [ESTIMARE]
P.joc_roata = 0.3e-3;  % jocul paletelor față de carcasă [m]                [ESTIMARE]
P.joc_comp = 5e-3;     % colectorul față de cilindru și chiulasă [m]       [ESTIMARE]
% Corpul cilindrului (pasul 12): aluminiu turnat, cămașa presată în el, prezoane M8 de la carter
% până la chiulasă (strâng și cilindrul, și chiulasa)
P.R_corp = 56e-3;    % raza exterioară a corpului cilindrului [m]: prezoanele la R48 + perete
P.prezon_trecere = 8.5e-3;  % găurile prezoanelor prin cilindru [m]
P.galerie_jos = 8e-3;  % galeria începe la atât deasupra bazei [m]           [ESTIMARE]
P.perete_cil = 4e-3;   % pereții corpului: exterior, între galerie și ferestre [m] [ESTIMARE]
P.canal_adancime = 14e-3;  % adâncimea radială a canalelor de transfer [m]   [ESTIMARE]
P.D_admisie = 25e-3;   % canalul colector - galerie și secțiunea colectorului [m] [ESTIMARE]

% --- Răcirea cu apă (s17; pasul 12 și chiulasa) ---
% Pompă electrică; apa trece întâi prin modulul de putere și capacul mașinii electrice (cea mai rece),
% apoi prin cilindru și chiulasă. Cămașa de apă a cilindrului stă deasupra ferestrelor (dedesubt sunt
% galeria și canalele), are forma unui C: în față rămâne plin în jurul ghilotinei evacuării. Apa ocolește
% coloanele prezoanelor pe interior (între coloană și cămașa cilindrului), ca la cilindrii cu prezoane în colțuri.
P.f_apa = 0.20;      % partea din puterea combustibilului care trece în apă [-] [ESTIMARE]
P.cp_apa = 3600; P.rho_apa = 1050;   % apă cu glicol 50% [J/kg K], [kg/m3]
P.dT_apa = 8;        % încălzirea apei prin motor [K]                        [ESTIMARE]
P.v_apa_max = 2.5;   % viteza maximă a apei în aluminiu (eroziune) [m/s]
P.R_apa_int = 36.5e-3;   % raza interioară a cămășii de apă: trecerea pe lângă coloanele prezoanelor [m]
P.apa_fata = 8e-3;   % plinul din față trece cu atât de marginea ferestrei de evacuare, pe fiecare parte [m]
P.apa_sus = 4e-3;    % apa se oprește cu atât sub punte [m]
P.n_gauri_punte = 5; P.d_gauri_punte = 7e-3;   % trecerile cilindru - chiulasă [-], [m]
P.unghi_gauri_punte = [70 110 180 -110 -70];   % pozițiile lor, de la evacuare [grade]
P.R_gauri_punte = 48.5e-3;    % raza lor: la mijlocul cămășii de apă [m]
P.D_racord_apa = 14e-3;  % racordurile și furtunurile circuitului [m]
P.unghi_intrare_apa = -120;   % intrarea în cilindru: radial, pe dreapta-spate (unghi de la evacuare) [grade]
% Evacuarea: tranziția dreptunghi-cerc, ștuțul cu inele O, urechile pentru arcuri, ghilotina
% Flanșa evacuării: placă cu doi prezoane M8 și garnitură (mai trainică decât ștuțul cu arcuri)
P.flansa_ev = [12 26 9 16]*1e-3;  % grosime în fața corpului, prezoanele la ±Y, raza bosajelor, filetul în aluminiu (2 d) [m] [ESTIMARE]
P.flansa_perete = 4e-3;           % peretele din jurul gurii [m]
P.lama_ev = [2.5 0.25 12 2]*1e-3;   % ghilotina: grosime, joc în fantă, cât rămâne în fantă la deschis, cât trece de fereastră pe fiecare parte [m]

% --- Capacul din dreapta, modulul de putere, prinderile pe cadru (s18; pasul 14 din Fusion) ---
% Capacul e un tambur turnat care alunecă peste rotor și se strânge pe un inel al semicarterului drept
% (capacul nu poate avea buză spre interior: n-ar trece de rotor). Statorul se prinde pe capac. În peretele
% exterior e camera de apă pe care stă modulul de putere (invertoarele mașinii de pe arbore și compresorului).
P.joc_rotor_capac = 5e-3;    % rotorul - capacul, radial și axial [m]
P.joc_bobine_capac = 3e-3;   % capetele bobinelor - fața interioară a capacului [m]  [ESTIMARE]
P.t_capac = 4e-3;            % peretele tamburului [m]                              [ESTIMARE]
P.t_inel_capac = 4e-3;       % inelul semicarterului drept pe care se strânge capacul [m] [ESTIMARE]
P.joc_corp_cil = 0.5e-3;     % capacul și inelul ocolesc corpul cilindrului (garnitură de cauciuc) [m] [ESTIMARE]
P.bosaj_stator = 12e-3;      % bosajele statorului pe capac, M5 în bucșe filetate [m]
P.apa_capac = [130 64 5]*1e-3;   % camera de apă: lungime (X), înălțime (Z), grosime (Y) [m] [ESTIMARE]
P.piele_capac = [3 4]*1e-3;  % pereții camerei: spre stator, sub modul [m]          [ESTIMARE]
P.modul = [90 60 25]*1e-3;   % modulul de putere: lungime, înălțime, grosime cu capac [m] [ESTIMARE]
P.eta_inv = 0.97;            % randamentul unui invertor de 48 V cu MOSFET [-]      [ESTIMARE]
P.R_jc = 0.15;               % jonctiune - talpa modulului, pe un invertor [K/W]     [ESTIMARE]
P.tim = [0.05e-3 3];         % pasta termică: grosime [m], conductivitate [W/m K]   [ESTIMARE]
P.mu_apa = 1.0e-3;  P.k_apa = 0.40;   % apă cu glicol 50% la ~75 °C: vâscozitate [Pa s], conductivitate [W/m K]
P.T_apa_modul = 75;          % apa la intrarea în modul (termostat + radiator) [grade C] [ESTIMARE]
P.Tj_max = 125;              % joncțiunea admisă a tranzistoarelor [grade C]
% Circuitul de apă, în ordinea curgerii (s17): pompa electrică la ieșirea radiatorului (apa cea mai rece, punctul cel
% mai de jos: fără cavitație), răcitorul de ulei, camera modulului din capacul drept, cilindrul (intră pe dreapta-spate),
% chiulasa, termostatul sus în față (punctul cel mai înalt: aerisire și bușon), radiatorul; ocolirea din termostat
% întoarce apa la pompă cât timp motorul e rece.
P.pompa_apa = [25 0.53e5; 35 0.25e5];   % curba pompei electrice de 12 V (clasa Pierburg CWA50): [L/min, Pa] [catalog]
P.furtun_apa = [14e-3 1.8];  % furtunurile: diametru interior, lungimea totală [m]   [ESTIMARE]
P.K_furtun = 6;              % coturi, intrări și ieșiri pe tot circuitul [-]          [ESTIMARE]
P.K_termostat = 4;           % termostatul deschis, raportat la furtun [-]             [ESTIMARE]
P.dp_radiator = 0.10e5;      % radiatorul la debitul nominal [Pa]                      [ESTIMARE]
P.aer_radiator = [8 25 35];  % aerul prin radiator: viteză [m/s], încălzire [K], temperatura lui [grade C] [ESTIMARE]
P.T_termostat = 82;          % deschiderea termostatului, la ieșirea din chiulasă [grade C] [ESTIMARE]
% Ungerea (s14): gerotor mecanic pe fusul stâng, între rulment și capacul pompei (MR-018); răcitorul ulei-apă pe plăcuța
% din fața băii din față. Sorbul rămâne la mijlocul tubului în U; galeriile spre pompă, răcitor și jeturi urmează (MR-009).
P.jet_ulei = [1.0 0.6 0.6]*1e-3;   % duzele: sub piston, palierul stâng, palierul drept [m] [ESTIMARE]
P.p_ulei = 2.5e5;            % presiunea la duze [Pa]                                  [ESTIMARE]
P.dp_ulei_traseu = 0.5e5;    % sorb, răcitor, galerii [Pa]                             [ESTIMARE]
P.Cd_jet = 0.7;  P.cp_ulei = 1900;   % coeficientul duzelor [-], căldura specifică a uleiului [J/kg K]
P.f_ulei = 0.012;            % partea din puterea combustibilului dusă de jetul de sub piston [-] [ESTIMARE]
P.P_rulmenti = 60;           % frecarea celor doi rulmenți paliere [W]                 [ESTIMARE]
P.gerotor = [0.80 0.80 46e-3 6e-3];  % pompa de ulei mecanică (MR-018): gerotor pe capătul stâng al arborelui, rotorul interior
                     % pe fusul Ø22; randamentul volumetric, randamentul total, Ø exterior, lățimea [m]; setul DE CONFIRMAT [ESTIMARE]
P.gerotor_joc = 0.5e-3;      % de la rulment la gerotor [m] [ESTIMARE]
P.capac_pompa_D = 62e-3;     % capacul pompei, cu simeringul în el, încastrat în bosajul rulmentului (Ø80) [m] [ESTIMARE]
P.p_ulei_ralanti = 1.0e5;    % presiunea la duzele rulmenților, la ralanti (jetul pistonului nu e necesar) [Pa] [ESTIMARE]
P.UA_racitor = 25;           % răcitorul ulei-apă cu plăci, mic [W/K]                  [ESTIMARE]
P.T_ulei_max = 110;          % uleiul la ieșirea din răcitor [grade C]                 [ESTIMARE]
P.galerie_sorb = 7e-3;       % galeria de aspirație [m]
P.nervura_sorb = [14 10]*1e-3;   % nervura de sub fund: lățime, înălțime [m]
P.y_sorb = -11e-3;           % galeria, în semicarterul drept [m]
P.racitor_ulei = [40 40 30]*1e-3;   % răcitorul de deasupra pompei: X, Y, Z [m]        [ESTIMARE]
P.rho_anexe = 2000;          % densitatea medie a pompelor și răcitorului (anvelopă) [kg/m3] [ESTIMARE]
% Prinderile pe cadru: urechi pe corpul rotund al carterului (față, spate), tijă la chiulasă, scut dedesubt
P.prindere = [10.5 6]*1e-3;  % gaura șurubului M10, peretele minim în jur [m]
P.ureche_carter = [66 28 30]*1e-3;   % centrul găurii (±X, Z) și jumătatea lățimii (Y) [m] [ESTIMARE]
P.ureche_chiulasa = [38 12 12]*1e-3; % centrul găurii (X, deasupra chiulasei) și lățimea (Y) [m] [ESTIMARE]
P.scut = [4 8]*1e-3;         % scutul de sub motor: grosime, jocul până la cel mai de jos punct [m] [ESTIMARE]

% --- Turații [rot/min] ---
P.n_ralanti = 1500; P.n_putere = 9500;
P.n_max   = 10500;   % limitatorul: segmentul de 0,8 mm nu se ridică până aici (s06)
P.n_supra = 11500;   % supraturarea de calcul (frână de motor peste limitator): regula de tensiune, rotorul

% --- Inerții [kg m2] ---
P.J_pasiv = 0.006;   % arbore + volant clasic                        [ESTIMARE]
% Volantul ușor nu mai e o estimare: arborele (s12, din Fusion) + rotorul mașinii (s15), vezi J_volant_usor.m

% --- Toba de rezonanță ---
P.gamma_ev = 1.35; P.R_ev = 287;                     % gazele de evacuare
P.EGT_ref = 600; P.EGT_min = 550; P.EGT_max = 650;   % [grade C] [ESTIMARE]
% Forma tobei (toba.m): Jennings, Two-Stroke Tuner's Handbook (1973), p. 55-73. Intervalele din carte, în paranteză:
% aria colectorului / fereastră (1,10-1,15), L1/D1 (6-8 la putere maximă), difuzorul: unghi inclus (7-8° la motocros
% <= 250 cm3), D2/D1 (2,5: aria de 6,25 ori), conul invers: unghi inclus (dublul difuzorului, 14-20°), D3/D1 (0,57-0,62),
% L5/D3 (12), reflexia: partea din conul invers până la punctul mediu de reflexie ("puțin peste jumătate")
P.toba_jennings = [1.10 7 8 2.5 16 0.60 12 0.55];
P.toba_tabla = 1.0e-3;        % tabla tobei [m] [ESTIMARE]
P.toba_joc = 15e-3;           % jocul minim al tobei față de restul motorului [m] [ESTIMARE]
P.toba_flansa = 6e-3;         % grosimea flanșei tobei [m] [ESTIMARE]
P.lambda_bosaj = [18 28 12]*1e-3;  % sonda lambda: filetul (M18 x 1,5, DE CONFIRMAT din fișa sondei), bosajul Ø și înălțimea [m] [ESTIMARE]
P.cat_joc = 5e-3;             % jocul catalizatorului rezervat în burtă; substratul DE CONFIRMAT (decizia D5) [m] [ESTIMARE]
P.toleranta_cvt  = 0.05;          % cât de precis ține variatorul turația (criteriul V8) [-]
P.banda_fara_cvt = [6000 10500];  % banda unei cutii cu trepte, pentru comparație [ESTIMARE]

% --- Variator CVT ---
P.C      = 0.150;    % distanța dintre axele fuliilor [m]: variatorul scurt, ca la EZ-9 (145 mm), cerut de bilanțul de volum s23 [ESTIMARE]
P.r1_min = 0.024;    % raza fuliei conducătoare, minimă [m]    [ESTIMARE]
P.r1_max = 0.054;    % raza fuliei conducătoare, maximă [m]    [ESTIMARE]
P.r2_max = 0.062;    % raza fuliei conduse la pornire [m]      [ESTIMARE]
P.beta   = 14;       % semiunghiul flancurilor curelei [grade] [ESTIMARE]

% --- Anvelopa EZ-9 și deciziile de ambalare (s23) [mm, grade] ---
P.ez9 = struct('WB', 1200, 'D_f', 484.8, 'D_s', 488, 'caster', 26, 'trail', 60, 'cursa_f', 100, 'cursa_s', 110, ...
               'GC', 210, 'sa', 750, 'L', 1680);
P.unghi_cil = 60;   % cilindrul față de verticală [grade]: decizia ta (26.11.2026), înlocuiește 30; s23 VL1–VL4 la acest unghi
P.V_rez = 5;        % rezervorul de benzină [L]: decizia C

% --- Vehicul ---
P.r_roata = 0.237;   % raza dinamică a roții spate de 10 inci (Ø 488 mm, ~3% strivire) [m] [ESTIMARE]
P.v_max   = 99;      % ținta (decizia D1: L3e-A1, 11 kW, valoarea dată de s19 cu Roots) [km/h]
P.P_ef    = 11e3;    % puterea efectivă la n_putere: limita L3e-A1, după care s-a ales imep_plin [W] [ESTIMARE]
P.P_A1    = [11e3 0.1e3];  % L3e-A1: putere maximă [W], raport putere/masă [W/kg] (Reg. UE 168/2013, anexa I)
P.m_veh   = [115 75];  % masa motocicletei în ordine de mers, masa pilotului [kg] [ESTIMARE]
P.CdA     = 0.55;    % aria frontală echivalentă, pilot în picioare/drept [m2] [ESTIMARE] [DE CONFIRMAT]
P.Crr     = 0.020;   % coeficientul de rezistență la rulare [-] [ESTIMARE]
P.eta_tr  = 0.85;    % randamentul transmisiei: variator, reducție, lanț [-] [ESTIMARE]
P.rho_aer = 1.2;     % densitatea aerului [kg/m3]

% --- Bateria (16 celule LFP) și mașina electrică ---
P.n_cel = 16; P.V_cel_min = 2.8; P.V_cel_nom = 3.2; P.V_cel_max = 3.65;  % [V]
% Celula aleasă (s20): A123 / Lithium Werks ANR26650M1B, fișa 26650 Power Cell (2022). Fișa dă 3,3 V nominal;
% V_cel_nom rămâne 3,2 V, deci energia din baterie.m e cu 3% sub cea din fișă.
P.n_par = 3;                                         % celule în paralel; s20 verifică curenții (BT1, BT2) și tensiunea la vârf (BT4)
P.cel_C_Ah = 2.5; P.cel_I_cont = 52; P.cel_I_puls = 120; P.cel_t_puls = 10;   % [Ah], [A], [A] timp de [s]
P.cel_I_inc = 10; P.cel_I_inc_puls = 26; P.cel_m = 0.076; P.cel_D = 25.96e-3; P.cel_L = 65.15e-3;   % [A], [A], [kg], [m], [m]
P.eta_isg = 0.90;   % ISG + invertor, motor sau generator [-] [ESTIMARE]
P.P_asist_max = 3.0e3;  % asistența ISG, mecanic [W]: decizia ta (26.11.2026), motorul + ISG <= 11 kW (L3e-A1), impusă de controler;
                        % 3 kW e ce ține pachetul 16s3p la capătul descărcării fără să coboare sub V_cel_min (BT4)
P.t_asist = 4;      % asistența la cuplul maxim [s], reperul PCX Hybrid [ESTIMARE]
P.P_aux   = [50 60 40];  % pompa de apă, ventilatorul radiatorului, ECU + servo + lumini LED [W] [ESTIMARE]
P.DoD     = 0.8;    % adâncimea de descărcare folosită [-] [ESTIMARE]
P.joc_pachet = 15e-3;    % BMS, bare, carcasă, pe fiecare latură a cutiei [m] [ESTIMARE]
P.cel_R = 10e-3;    % rezistența internă: fișa dă impedanța la 1 kHz sub 10 mOhm; cea în curent continuu la 10 s nu e dată [Ohm] [ESTIMARE]
P.I_pk    = 380;     % curentul de fază de vârf [A]: controlerul ales; volantul activ (s05)
P.r_rot   = 0.060;   % raza interioară a paharului (= exteriorul magneților) [m] [ESTIMARE]
P.t_pahar = 0.0075;  % grosimea paharului de oțel în dreptul magneților: închide fluxul fără saturație (s15) [m]
P.t_pahar_subtire = 0.003;   % paharul în afara magneților (acolo nu trece flux): mai ușor [m] [ESTIMARE]
P.t_mag   = 0.004;   % grosimea magneților [m]                 [ESTIMARE]
% Mașina electrică (s15; pașii 10 din Fusion): rotor exterior de oțel cu magneți NdFeB lipiți
% în pahar, stator din tole cu bobine concentrate pe dinți. 12 crestături / 14 poli: factor de
% înfășurare 0,933, cuplu de agățare mic, bobine scurte. Rotorul stă pe conul arborelui, cu
% paharul deschis spre exterior; statorul se prinde de capacul din dreapta (scurtează consola
% arborelui, iar capacul de aluminiu răcește statorul și scoate firele direct).
P.Q_isg = 12;  P.p_isg = 7;          % crestături, perechi de poli
P.g_isg = 0.7e-3;                    % întrefierul [m]                             [ESTIMARE]
P.alfa_mag = 0.83;                   % arcul magnetului / pasul polar [-]          [ESTIMARE]
P.Br20 = 1.30;  P.alfa_Br = -0.0012; % NdFeB N42SH: inducția remanentă [T], coeficientul [1/K]
P.Hcj20 = 1592e3;  P.alfa_Hcj = -0.006;  % câmpul coercitiv intrinsec [A/m], coeficientul [1/K]
P.mu_rec = 1.05;  P.T_mag = 120;     % permeabilitatea de recul; magneții calzi [grade C] [ESTIMARE]
P.k_Carter = 1.1;                    % coeficientul Carter al crestăturilor        [ESTIMARE]
P.B_max = [1.7 1.5 1.6];             % inducția admisă: dinte, jugul statorului, paharul [T]
P.J_max = 25e6;  P.k_umplere = 0.55; % densitatea de curent de scurtă durată [A/m2]; umplerea crestăturii (bobine preformate)
P.h_varf = 1.5e-3;  P.b_desch = 2.5e-3;  % înălțimea vârfului dintelui, deschiderea crestăturii [m]
P.tola = 0.2e-3;                     % tole NO20 (frecvența de 1,3 kHz la supraturare) [m]
P.joc_capete = 2e-3;                 % de la capetele bobinelor la discul rotorului [m] [ESTIMARE]
P.t_disc = 5e-3;  P.R_butuc = 16e-3; % discul rotorului; raza butucului de pe con [m] [ESTIMARE]
P.ureche_stator = [8 10 5.5]*1e-3;   % 3 urechi de prindere: lungime spre interior, lățime, gaura M5 [m]
P.saiba_rotor = [12.5 24 2.5]*1e-3;  % șaiba piuliței: interior, exterior, grosime [m]
P.piulita = [17 10]*1e-3;            % piulița M12 x 1,25: cheie 17, înălțime 10 [m]
P.rho_tole = 7650;  P.rho_cu = 8960;  P.rho_izolatie = 1300;   % [kg/m3]
P.rho_otel = 7850; P.rho_mag = 7500; P.rho_al = 2700;   % [kg/m3]
P.Re_otel  = 275e6;  % limita de curgere, oțel S275 [Pa]
P.tau_isg  = 0.5e-3; % constanta de timp a cuplului electric [s] [ESTIMARE]
end
