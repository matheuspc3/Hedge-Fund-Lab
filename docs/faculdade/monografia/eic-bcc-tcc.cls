%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% LaTeX Class for Bachelor's Thesis
% Cefet/RJ - Computer Science undergraduate course
% Version: 2025/06/26
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{eic-bcc-tcc}[2025/06/27 Cefet/RJ EIC BCC]

% Base class: report with 12pt font and A4 paper
\LoadClass[12pt,a4paper]{report}



% =================================================
% 1. ESSENTIAL PACKAGES
% =================================================

% Language and localization
\RequirePackage[brazil]{babel}          % Brazilian Portuguese language support
% \RequirePackage[brazilian]{backref}     % Back references in bibliography
\RequirePackage{datetime2}             % Date/time formatting

% Font and encoding
\RequirePackage[T1]{fontenc}            % Improved font encoding
\RequirePackage[utf8]{inputenc}        % UTF-8 input encoding

% Page layout and formatting
\RequirePackage[lmargin=3cm,rmargin=2cm,tmargin=3cm,bmargin=2cm,headheight=14.5pt]{geometry} % Page margins
\RequirePackage{fancyhdr}               % Custom headers/footers
\RequirePackage{setspace}               % Line spacing control
\RequirePackage{indentfirst}            % Indent first paragraph
\RequirePackage{ragged2e}               % Improved text alignment

% Tables and figures
\RequirePackage{amsmath}                % Mathematical formulas
\RequirePackage{amssymb}                % Additional mathematical symbols
\RequirePackage{booktabs}               % Professional-quality tables
\RequirePackage{graphicx}               % Enhanced graphics support
\RequirePackage{float}                  % Improved float handling
\RequirePackage[font=small,font=bf]{caption} % Custom captions
\RequirePackage{array}                  % For table column types
\RequirePackage{multirow}               % Multi-row cells in tables
\RequirePackage{comment}                % Block comments

% Acronyms
\PassOptionsToPackage{nolocale,lang-warn=false}{datatool-base}
\RequirePackage[acronym,nomain]{glossaries} % List of acronyms

% Document structure
\RequirePackage{titlesec}               % Custom section titles
\RequirePackage{titletoc}               % Custom table of contents
\RequirePackage{tocloft}                % More TOC customization
\RequirePackage[nottoc,notlof,notlot]{tocbibind} % Add TOC to TOC

% Utilities
\RequirePackage{etoolbox}               % Macro manipulation
\RequirePackage{ifthen}                 % Conditional commands
\RequirePackage{lastpage}               % Reference to last page
\RequirePackage{pdfpages}               % Include PDF documents
\RequirePackage{textcase}               % Text case transformations
\RequirePackage[hyphens,obeyspaces]{url}           % URL formatting with hyphenation
\RequirePackage[square,authoryear]{natbib}         % Citation formatting
\RequirePackage[portuguese,ruled,linesnumbered,algochapter,titlenumbered]{algorithm2e}
\RequirePackage{hyperref}               % Handle PDF bookmarks and links


% =================================================
% 2. GENERAL SETTINGS
% =================================================

\hbadness=20000                  % For underfull hbox errors
\hfuzz=5pt                       % For overfulls errors
\emergencystretch=2em            % Help TeX resolve long lines without overflow

% Paragraph formatting
\setlength\parindent{1.5cm}   % Paragraph indentation
\onehalfspacing               % 1.5 line spacing

% Plain page formatting
\fancypagestyle{plain}{%
  \fancyhf{}
  \fancyhead[R]{\thepage}
  \renewcommand{\headrulewidth}{0pt}
}

% Page formatting
\pagestyle{fancy}
\fancyhf{}  % Remove header and footer
\fancyhead[R]{\thepage} % Page number in the right header
\renewcommand{\headrulewidth}{0pt}  % remove horizontal line from header

% Caption settings
\captionsetup[table]{skip=12pt}  % Space after table captions
\captionsetup[figure]{skip=12pt} % Space after figure captions

% Leader dots configuration for TOC
\newcommand{\setupdotfill}{%
  \renewcommand{\cftdot}{.}           % Dot character
  \renewcommand{\cftdotsep}{1}       % Dot spacing
  \renewcommand{\cftchapdotsep}{\cftdotsep} % Chapters
  \renewcommand{\cftsecdotsep}{\cftdotsep}   % Sections
  \renewcommand{\cftsubsecdotsep}{\cftdotsep} % Subsections
  \renewcommand{\cftsubsubsecdotsep}{\cftdotsep} % Subsubsections
  \renewcommand{\cftparadotsep}{\cftdotsep} % Paragraphs
}
\setupdotfill % Apply the configuration

% links formatting
\hypersetup{
  hidelinks,          % Remove borders around links
  plainpages=false,   % Avoid duplicate page anchors
  hypertexnames=false,% Avoid duplicate anchors after page/chapter counter resets
  unicode=true        % Better support for unicode
}
\urlstyle{same} % Usa a mesma fonte do texto normal
\Urlmuskip=0mu plus 2mu
\def\UrlLeft{}
\def\UrlRight{}



% =================================================
% 3. CUSTOM COMMANDS AND ENVIRONMENTS
% =================================================

% -------------------------
% 3.1 Student Commands
% -------------------------

% \addstudent{role}{name} - Adds a student
% Example: \addstudent[Full Name]{Nome Completo}
\newcommand{\addstudent}[2][]{
  \@ifundefined{@studentlist}
  {
    \gdef\@studentlist{#2}
    \gdef\@studentlines{#2}
    % set english names
    \ifblank{#1}{
      \gdef\@studentlisten{#2}
    }{
      \gdef\@studentlisten{#1}
    }
  }{
    \g@addto@macro\@studentlist{, #2}
    \g@addto@macro\@studentlines{\\ #2}
    % set english names
    \ifblank{#1}{
      \g@addto@macro\@studentlisten{, #2}
    }{
      \g@addto@macro\@studentlisten{, #1}
    }
  }
}

% -------------------------
% 3.2 Advisor Commands
% -------------------------

% \advisor[gender]{name} - Sets thesis advisor
% Example: \advisor[f]{Maria Silva} (female advisor)
\newcommand{\advisor}[2][m]{% 
  \ifthenelse{\equal{#1}{f}}{
    \gdef\@orientadortitle{Orientadora} % Female
  }{
    \gdef\@orientadortitle{Orientador}  % Male
  }
  \gdef\@orientadorname{#2}
  \gdef\@orientadorfull{\@orientadortitle: \@orientadorname}
  \addboardmember{\@orientadortitle}{\@orientadorname}
}

% \coadvisor[gender]{name} - Sets co-advisor
% Example: \coadvisor{João Santos} (default male)
\newcommand{\coadvisor}[2][m]{%
  \ifthenelse{\equal{#1}{f}}{
    \gdef\@coorientadortitle{Coorientadora} % Female
  }{
    \gdef\@coorientadortitle{Coorientador}  % Male
  }
  \gdef\@coorientadorname{#2}
  \gdef\@coorientadorfull{\@coorientadortitle: \@coorientadorname}
  \addboardmember{\@coorientadortitle}{\@coorientadorname}
}

% -------------------------
% 3.3 Title and Metadata
% -------------------------

% \titleen{title} - Sets English title for abstract
% Example: \titleen{My Thesis Title in English}
\newcommand{\titleen}[1]{\gdef\@englishtitle{#1}}

% Keywords commands
\newcommand{\palavraschave}[1]{\vspace{1em}\par\noindent\textbf{Palavras-chave:} #1}
\newcommand{\keywords}[1]{\vspace{1em}\par\noindent\textbf{Keywords:} #1}
\newcommand{\citeonline}{\citet}



% =================================================
% 4. TITLE FORMATTING
% =================================================

% Primary title formatting (chapter)
\titleformat{\chapter}
  {\normalfont\bfseries\uppercase} % format
  {\large\thechapter}              % label
  {1em}                            % sep
  {\large}                         % before code
\titlespacing*{\chapter}{0pt}{-30pt}{30pt} % spacing

% Secondary title formatting (section)
\titleformat{\section}
  {\normalfont\uppercase} % format
  {\thesection}           % label
  {1em}                   % sep
  {}                      % before code
\titlespacing*{\section}{0pt}{3em}{0pt}

% Tertiary title formatting (subsection)
\titleformat{\subsection}
  {\normalfont}     % format
  {\thesubsection}  % label
  {1em}             % sep
  {}                % before code
\titlespacing*{\subsection}{0pt}{1.5em}{0pt}

% Quaternary title formatting (subsubsection)
\titleformat{\subsubsection}
  {\normalfont}        % format
  {\thesubsubsection}  % label
  {1em}                % sep
  {}                   % before code
\titlespacing*{\subsubsection}{0pt}{1.5em}{0pt}

% Quinary title formatting (paragraph)
\titleformat{\paragraph}
  {\normalfont\itshape}  % format
  {\theparagraph}        % label
  {1em}                  % sep
  {}                     % before code
\titlespacing*{\paragraph}{0pt}{1.5em}{0pt}



% =================================================
% 5. FRONT MATTER ELEMENTS
% =================================================

% -------------------------
% 5.1 Dedication Page
% -------------------------
% Example usage:
% \begin{dedicatoria}
%   To my family...
% \end{dedicatoria}
\newenvironment{dedicatoria}
{
  \cleardoublepage
  \thispagestyle{empty}
  \vspace*{18cm}
  \begin{flushright}
    \begin{minipage}{0.5\textwidth}
      \raggedleft\normalsize
}
{
    \end{minipage}
  \end{flushright}
  \cleardoublepage
}

% -------------------------
% 5.2 Acknowledgments
% -------------------------
\newenvironment{agradecimentos}
{
  \cleardoublepage
  \begin{center}
    \bfseries\large AGRADECIMENTOS
  \end{center}
  \vspace{10pt}
  \thispagestyle{empty}
  \par
}
{
  \cleardoublepage
}

% -------------------------
% 5.3 Abstract (Portuguese)
% -------------------------
\newenvironment{resumo}
{
  \cleardoublepage
  \begin{center}
    \bfseries\large RESUMO
  \end{center}
  \vspace{10pt}
  \@studentlist. \textbf{\@title}. \@date. \pageref{LastPage}. Trabalho de Conclusão de Curso – Centro Federal de Educação Tecnológica Celso Suckow da Fonseca. Rio de Janeiro. Cidade, \@date.\\[1cm]
  \thispagestyle{empty}
}
{
  \cleardoublepage
}

% -------------------------
% 5.4 Abstract (English)
% -------------------------
\renewenvironment{abstract}
{
  \cleardoublepage
  \begin{center}
    \bfseries\large ABSTRACT
  \end{center}
  \vspace{10pt}
  \ifdef{\@studentlisten}%
  {\@studentlisten}{\@studentlist}.
  \textbf{\@englishtitle}. \@date. \pageref{LastPage}. Undergratuade Thesis – Federal Center of Technological Education. Rio de Janeiro. City, \@date.\\[1cm]
  \thispagestyle{empty}
}
{
  \cleardoublepage
}



% =================================================
% 6. TITLE PAGES
% =================================================

% Main title page command
\renewcommand{\maketitle}{%
\begin{titlepage}
  \begin{center}
    \bfseries\large
    CENTRO FEDERAL DE EDUCAÇÃO TECNOLÓGICA CELSO SUCKOW DA FONSECA\\[1.5em]
    COORDENAÇÃO DO CURSO DE BACHARELADO EM CIÊNCIA DA COMPUTAÇÃO\\\vfill
    
    \MakeUppercase{\@studentlines}\\\vfill
    
    \large\MakeUppercase{\@title}\\\vfill
    
    TRABALHO DE CONCLUSÃO DE CURSO\\\vfill
    
    RIO DE JANEIRO\\[1.5cm]
    \@date
  \end{center}
\end{titlepage}

\begin{titlepage}
  \begin{center}
    \bfseries\large
    \MakeUppercase{\@studentlines}\\\vfill
    
    \large\MakeUppercase{\@title}\\\vfill
  \end{center}
  
  \begin{flushright}
    \normalfont\normalsize
    \begin{minipage}{0.5\textwidth}
      \justifying\noindent
      Trabalho de Conclusão de Curso apresentado como requisito parcial à obtenção do título de Bacharel em Ciência da Computação, da Coordenação do curso de Bacharelado em Ciência da Computação, do Centro Federal de Educação Tecnológica Celso Suckow da Fonseca.\\[1.5cm]
      
      
      \noindent\@orientadorfull
      \ifdefined\@coorientadorfull
        \\\@coorientadorfull
      \fi
    \end{minipage}\\\vfill
  \end{flushright}
  
  \begin{center}
    \bfseries\large
    RIO DE JANEIRO\\[1.5cm]
    \@date
  \end{center}
\end{titlepage}

% Include approval form if exists
\IfFileExists{ficha.pdf}
{\includepdf{ficha.pdf}}{}
}



% =================================================
% 7. EXAMINATION COMMITTEE
% =================================================

\newcommand{\@bancamembers}{} % Stores committee members

% \addboardmember{role}{name} - Adds committee member
% Example: \addbancamember{Membro Interno}{Prof. Dr. Silva}
\newcommand{\addboardmember}[2]{
  \g@addto@macro\@bancamembers{
    \rule{\textwidth}{0.4pt}\\
    #1 - #2\\[1cm]
  }
}

% \makeapproval - Generates approval page
\newcommand{\makeapproval}{
  \IfFileExists{termo.pdf}
  {\includepdf{termo.pdf}}
  {
    \cleardoublepage
    \thispagestyle{empty}
    \begin{center}
      \bfseries\large
      TERMO DE APROVAÇÃO\\[1.5cm]
    \end{center}
    
    \noindent\textbf{Título:} \@title\\[0.5cm]
    \noindent\textbf{Discente(s):} \@studentlist\\[1cm]
  
    \noindent\textbf{Data de aprovação:} \rule{3cm}{0.4pt}\\[1.5cm]
  
    \noindent\textbf{Banca Examinadora:}\\[1cm]
    
    \noindent
    \@bancamembers
  
    \vfill
    \begin{center}
      \footnotesize
      A Folha de Aprovação assinada encontra-se na Coordenação do Curso
    \end{center}
  }
}



% =================================================
% 8. LISTS AND TABLES OF CONTENTS
% =================================================

% -------------------------
% 8.1 Figures
% -------------------------
% List of figures title configuration
\renewcommand{\cftloftitlefont}{\hfill\large\bfseries\MakeUppercase}
\renewcommand{\cftafterloftitle}{\hfill}
\setlength{\cftbeforeloftitleskip}{-18pt}
\setlength{\cftafterloftitleskip}{22pt}

% Figure caption configuration in the list
\renewcommand{\cftfigpresnum}{Figura~}
\settowidth{\cftfignumwidth}{\hspace{50pt}}
\renewcommand{\cftfigaftersnumb}{~-~}

% Creates the page with the list of figures
\newcommand{\listoffigurespage}{
  \cleardoublepage
  \let\ps@plain\ps@empty
  \listoffigures
  \cleardoublepage
  \pagestyle{plain}
}

% -------------------------
% 8.2 Tables
% -------------------------
% List of tables title configuration
\renewcommand{\cftlottitlefont}{\hfill\bfseries\large\MakeUppercase} 
\renewcommand{\cftafterlottitle}{\hfill}
\setlength{\cftbeforelottitleskip}{-18pt}
\setlength{\cftafterlottitleskip}{22pt}

% Table caption configuration in the list
\renewcommand{\cfttabpresnum}{Tabela~}
\settowidth{\cfttabnumwidth}{\hspace{60pt}}
\renewcommand{\cfttabaftersnum}{~-~}

% Creates the page with the list of tables
\newcommand{\listoftablespage}{
  \cleardoublepage
  \let\ps@plain\ps@empty
  \listoftables
  \cleardoublepage
}

% Creates new column types for tables
\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcommand\Tstrut{\rule{0pt}{2.6ex}}
\newcommand\Bstrut{\rule[-0.9ex]{0pt}{0pt}}
\newcommand{\specialcell}[2][c]{%
  \begin{tabular}[#1]{@{}c@{}}#2\end{tabular}}

% -------------------------
% 8.3 Table of Acronyms
% -------------------------
% Glossaries configuration
\renewcommand{\glossarysection}[2][\glossarytoctitle]{%
  \cleardoublepage
  \pagestyle{empty}
  \vspace*{-35pt}
  \begin{center}
    \large\bfseries\MakeUppercase{LISTA DE ACRÔNIMOS}
  \end{center}
  \vspace{0pt}
}
\renewcommand{\glsnamefont}[1]{\textbf{#1}} % Format list of acronyms
\setlength{\glsdescwidth}{0.8\textwidth}    % Description column width
% Create new list style for acronyms without page reference
\newglossarystyle{linkednoindex}{%
  \setglossarystyle{list}%
  \renewcommand{\glossentry}[2]{%
    \item[\glsentryitem{##1}\glstarget{##1}{\glossentryname{##1}}]
    \glossentrydesc{##1}%
  }%
}

% Create new glossary for acronyms
\newglossary[slg]{acronyms}{acr}{acn}{LISTA DE ACRÔNIMOS}

% Creates the page with the list of acronyms
\newcommand{\listofacronymspage}{%
  \cleardoublepage
  \begingroup
  \let\ps@plain\ps@empty
  \pagestyle{empty}
  \printglossary[type=\acronymtype, title=LISTA DE ACRÔNIMOS, style=linkednoindex]
  \cleardoublepage
  \endgroup
}

% Enable the glossary system
\makeglossaries

% Configure hiperlinks for acronym
\renewcommand*{\glstextformat}[1]{\textcolor{black}{#1}} % Remove link color

% -------------------------
% 8.4 Table of Contents
% -------------------------
% TOC title configuration
\renewcommand{\cfttoctitlefont}{\hspace{0.4\textwidth}\large\bfseries\MakeUppercase}
\renewcommand{\cftaftertoctitle}{}
\setlength{\cftbeforetoctitleskip}{-18pt}
\setlength{\cftaftertoctitleskip}{22pt}

% TOC elements formatting
\patchcmd{\l@chapter}{#1}{\MakeTextUppercase{#1}}{}{}
\patchcmd{\l@section}{#1}{\MakeTextUppercase{#1}}{}{}
\patchcmd{\l@subsection}{#1}{\MakeTextUppercase{#1}}{}{}
\patchcmd{\l@paragraph}{#1}{\itshape #1}{}{}

% TOC elements spacing
\setlength{\cftsecindent}{0pt}
\setlength{\cftsubsecindent}{0pt}
\setlength{\cftsubsubsecindent}{0pt}
\setlength{\cftparaindent}{0pt}

% Define the depth, i.e., elements to present (until paragraph)
\setcounter{secnumdepth}{5}
\setcounter{tocdepth}{5}

% Creates the page with the TOC
\newcommand{\tableofcontentspage}{
  \cleardoublepage
  \let\ps@plain\ps@empty
  \tableofcontents
  \cleardoublepage
}



% =================================================
% 9. APPENDICES AND ANNEXES
% =================================================

% \appendix - Configures appendix formatting
\let\oldappendix\appendix
\renewcommand{\appendix}{%
  \oldappendix
  \renewcommand{\appendixname}{APÊNDICE}
  \setcounter{chapter}{0} % restart numbering
  
  % appendix formatting
  \renewcommand{\thechapter}{\Alph{chapter}}  % letters instead of numbers
  \titleformat{\chapter}  % add APÊNDICE before the appendix title
    {\normalfont\large\bfseries\centering}
    {\appendixname~\thechapter~--~}
    {0pt}
    {\large\MakeUppercase}
  \titlespacing*{\chapter}{0pt}{25em}{0pt}  % centers in new page
  
  % format how it appears in TOC
  \titlecontents{chapter}[0pt]% identation
    {\addvspace{12pt}\bfseries}% format before title
    {\MakeUppercase\appendixname~\thecontentslabel~-~}% num chapter
    {}% star chapter
    {\titlerule*[0.5pc]{.}\contentspage}% rule and number
}

% \anexos - Configures annexes formatting
\newcommand{\anexos}{%
  \cleardoublepage
  \renewcommand{\appendixname}{ANEXO}
  \setcounter{chapter}{0} % restart numbering
  
  % annex formatting
  \renewcommand{\thechapter}{\Alph{chapter}}  % letters instead of numbers
  \titleformat{\chapter}  % add ANEXO before the appendix title
    {\normalfont\large\bfseries\centering}
    {\appendixname~\thechapter~--~}
    {0pt}
    {\large\MakeUppercase}
  \titlespacing*{\chapter}{0pt}{25em}{0pt}  % centers in new page

  % format how it appears in TOC
  \titlecontents{chapter}[0pt]% identation
    {\addvspace{12pt}\bfseries}% format before title
    {ANEXO~\thecontentslabel~-~}% num chapter
    {}% star chapter
    {\titlerule*[0.5pc]{.}\contentspage}% rule and number
}

% Redefines chapter command to consider whe in backmatter
\let\oldchapter\chapter
\renewcommand{\chapter}{%
  \ifboolexpe{%
    test {\ifdef{\@atbackmatter}}%
  }%
  {%
    \@ifstar{\@chapterstar}{\@chapterbackmatter}%
  }{%
    \oldchapter
  }%
}

\newcommand{\@chapterstar}[1]{%
  \oldchapter*{#1}%
}

\newcommand{\@chapterbackmatter}[1]{%
  \oldchapter{#1}%
  \cleardoublepage  % start the appendix or annex text in new page
}



% =================================================
% 10. DOCUMENT STRUCTURE COMMANDS
% =================================================

% \mainmatter - Starts main content
\newcommand{\mainmatter}{%
  \cleardoublepage
  \pagenumbering{arabic}
  \setcounter{page}{1}
  \fancypagestyle{plain}{%
    \fancyhf{}
    \fancyhead[R]{\thepage}
    \renewcommand{\headrulewidth}{0pt}
  }
  \pagestyle{plain}
}

% \backmatter - Starts back matter
\newcommand{\backmatter}{%
    \cleardoublepage
    \pagestyle{plain}
    \gdef\@atbackmatter{true}
}



% =================================================
% 11. BIBLIOGRAPHY FORMATTING
% =================================================
% avoid errors with missing keys in citation
\providecommand{\abntnextkey}{}

% \referencepage - Starts the references
\newcommand{\referencepage}{%
  \bibliographystyle{apalike}
  \renewcommand{\bibname}{\MakeUppercase{Referências}}
  \renewcommand\bibsection{
    \cleardoublepage
    \begin{center}
      \bfseries\large\bibname
    \end{center}
    \vspace{10pt}
    \addcontentsline{toc}{chapter}{\bibname}
  }
  \bibliography{references}
}
