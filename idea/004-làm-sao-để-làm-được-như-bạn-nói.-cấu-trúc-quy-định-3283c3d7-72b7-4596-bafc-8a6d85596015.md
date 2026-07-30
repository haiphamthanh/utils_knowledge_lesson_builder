# Conversation 4

- Channel ID: 6a659ef4-5f00-83ec-b9a9-83e920751b84
- URL: https://chatgpt.com/g/g-p-6a081fb0df948191bd4f44b424a2c66d/c/6a659ef4-5f00-83ec-b9a9-83e920751b84
- User Turn ID: 074c6d38-6587-48e9-9dd3-8f597d64304a
- Assistant Turn ID: 3283c3d7-72b7-4596-bafc-8a6d85596015
- Saved At: 2026-07-30T15:03:04.564Z

## Message

làm sao để làm được như bạn nói. cấu trúc quy định script build. guideline cho agent hay template và các vấn đề liên quan cần thiết kế và bố trí lại cho phù hợp không?

## Response

Đúng, cần bố trí lại cấu trúc, metadata, template, guideline cho agent và script build. Không nên để một file cookbook.yml vừa quản lý thứ tự đọc, vừa đại diện cho quan hệ tri thức.
Thiết kế phù hợp nhất là tách hệ thống thành ba lớp:
Lesson content
Knowledge graph
Learning path
Trong đó:

Lesson lưu nội dung kiến thức độc lập.

Knowledge graph lưu quan hệ thật giữa các chủ đề.

Learning path quyết định thứ tự xuất hiện trong một cookbook cụ thể.

Knowledge Cookbook — Project Design1. Mục tiêu thiết kếHệ thống cần đồng thời đáp ứng hai nhu cầu:Tổ chức tri thức đúng theo quan hệ tự nhiên giữa các khái niệm.Xuất bản cookbook có trình tự đọc rõ ràng, không làm người đọc bị lạc khỏi chủ đề chính.Vì vậy, hệ thống không dùng trực tiếp knowledge graph để quyết định thứ tự PDF.Thay vào đó:Knowledge Graph
    Quản lý quan hệ giữa các kiến thức

Learning Path
    Quản lý thứ tự học và thứ tự xuất bản

Lesson
    Quản lý nội dung của từng chủ đềMột lesson có thể được sử dụng trong nhiều learning path khác nhau mà không cần sao chép nội dung.2. Cấu trúc projectknowledge-cookbook/
├── README.md
├── build.sh
├── requirements.txt
│
├── templates/
│   ├── book.tex
│   ├── lesson.tex
│   └── chapter-intro.tex
│
├── guidelines/
│   ├── authoring.md
│   ├── learning-path.md
│   ├── knowledge-graph.md
│   └── agent-instructions.md
│
├── scripts/
│   ├── build.py
│   ├── validate.py
│   └── create_lesson.py
│
├── src/
│   ├── artificial-intelligence/
│   │   ├── cookbook.yml
│   │   ├── graph.yml
│   │   ├── paths/
│   │   │   ├── foundation.yml
│   │   │   └── complete.yml
│   │   └── lessons/
│   │       ├── ai-overview.tex
│   │       ├── machine-learning.tex
│   │       ├── neural-network.tex
│   │       ├── activation-function.tex
│   │       └── transformer.tex
│   │
│   └── system-design/
│       ├── cookbook.yml
│       ├── graph.yml
│       ├── paths/
│       └── lessons/
│
└── build/Độ sâu chính là:src/<cookbook>/lessons/<lesson>.tex
src/<cookbook>/paths/<path>.ymlĐây vẫn là cấu trúc tương đối nông. Hai thư mục lessons và paths có ý nghĩa rõ ràng, không tạo ra phân cấp kỹ thuật không cần thiết.3. Vai trò của các fileFileVai tròcookbook.ymlMetadata chung của lĩnh vựcgraph.ymlQuan hệ giữa các lessonpaths/*.ymlCác trình tự đọc khác nhaulessons/*.texNội dung độc lập của từng chủ đềtemplates/book.texKhung PDFtemplates/lesson.texTemplate tạo lessonvalidate.pyKiểm tra cấu trúc và quan hệbuild.pySinh file LaTeX tổng và PDFcreate_lesson.pyTạo lesson mới đúng chuẩnagent-instructions.mdQuy định cho AI agent4. File cookbook.ymlFile này chỉ chứa metadata chung, không chứa danh sách bài học theo thứ tự.id: artificial-intelligence

title: "Artificial Intelligence Cookbook"

subtitle: >
  Các khái niệm, kỹ thuật và sự phát triển của hệ thống
  trí tuệ nhân tạo.

author: "a Biển"

language: vi

default_path: foundation

description: >
  Cookbook giải thích AI theo hướng nhu cầu, vấn đề,
  kỹ thuật giải quyết, hạn chế và nhu cầu phát sinh tiếp theo.default_path xác định learning path mặc định khi người dùng không chỉ định path.5. File graph.ymlKnowledge graph chỉ mô tả quan hệ tri thức.nodes:
  ai-overview:
    title: "Tổng quan về AI"

  machine-learning:
    title: "Machine Learning"

  neural-network:
    title: "Neural Network"

  activation-function:
    title: "Activation Function"

  backpropagation:
    title: "Backpropagation"

  transformer:
    title: "Transformer"

relations:
  - from: machine-learning
    to: ai-overview
    type: part_of

  - from: neural-network
    to: machine-learning
    type: builds_on

  - from: activation-function
    to: neural-network
    type: component_of

  - from: backpropagation
    to: neural-network
    type: explains

  - from: transformer
    to: neural-network
    type: builds_onCác loại relation nên được giới hạn để tránh agent tự phát sinh tùy tiện.requires
builds_on
part_of
component_of
explains
applies
contrasts_with
related_to
leads_toÝ nghĩa:RelationÝ nghĩarequiresPhải hiểu bài kia trướcbuilds_onPhát triển từ kiến thức trướcpart_ofLà một phần của chủ đề lớn hơncomponent_ofLà thành phần kỹ thuậtexplainsGiúp giải thích cơ chếappliesỨng dụng khái niệm kháccontrasts_withSo sánh với một phương pháp khácrelated_toCó liên quan nhưng không phụ thuộcleads_toLàm phát sinh nhu cầu tiếp theoKhông nên sử dụng related_to thay cho mọi quan hệ. Agent phải chọn quan hệ cụ thể nhất có thể.6. Learning pathLearning path quyết định nội dung và thứ tự build PDF.Ví dụ paths/foundation.yml:id: foundation

title: "AI Foundation"

description: >
  Lộ trình dành cho người mới, ưu tiên hiểu bức tranh tổng thể
  trước khi đi sâu vào từng kỹ thuật.

audience: beginner

chapters:
  - id: overview
    title: "Bức tranh tổng thể"

    objective: >
      Hiểu AI, Machine Learning, Deep Learning và LLM liên hệ
      với nhau như thế nào.

    lessons:
      - ai-overview
      - machine-learning-overview
      - deep-learning-overview
      - llm-overview

  - id: machine-learning-foundation
    title: "Nền tảng Machine Learning"

    objective: >
      Hiểu cách hệ thống học từ dữ liệu và các dạng bài toán cơ bản.

    lessons:
      - machine-learning
      - supervised-learning
      - unsupervised-learning
      - model-evaluation

  - id: neural-network-foundation
    title: "Nền tảng Neural Network"

    objective: >
      Hiểu các thành phần chính tạo nên một mạng neural.

    lessons:
      - neural-network
      - activation-function
      - loss-function
      - backpropagationTrong khi đó, paths/complete.yml có thể chi tiết hơn:id: complete

title: "Complete AI Knowledge Path"

audience: intermediate

chapters:
  - id: foundations
    title: "Foundations"
    lessons:
      - ai-overview
      - machine-learning
      - supervised-learning
      - regression
      - classification
      - model-evaluation

  - id: neural-networks
    title: "Neural Networks"
    lessons:
      - neural-network
      - activation-function
      - loss-function
      - gradient-descent
      - backpropagation
      - regularizationNhư vậy, cùng một bài:machine-learning.texcó thể được dùng trong:foundation.yml
complete.yml
researcher.yml
software-engineer.ymlnhưng mỗi path có thứ tự và phạm vi khác nhau.7. Không dùng graph để tự động topo-sort toàn bộ cookbookTopological sorting chỉ nên dùng để:kiểm tra dependency;phát hiện bài được đặt trước prerequisite;gợi ý vị trí phù hợp;phát hiện dependency cycle.Không nên dùng topo-sort để tự quyết định toàn bộ thứ tự PDF.Ví dụ:Neural Network
 ├── Activation Function
 ├── Loss Function
 ├── Gradient Descent
 ├── Backpropagation
 └── RegularizationGraph có thể sắp cả năm bài này sau Neural Network, nhưng không biết bài nào cần xuất hiện trước để người mới dễ hiểu.Learning path phải do người thiết kế hoặc agent có guideline rõ ràng quyết định.Quy tắc:Graph validates the path.
Graph does not author the path.8. Template lessonMỗi lesson nên chứa metadata ở đầu file dưới dạng comment LaTeX.%---
% id: activation-function
% title: Activation Function
% level: foundation
% status: complete
% prerequisites:
%   - neural-network
% tags:
%   - neural-network
%   - deep-learning
% related:
%   - loss-function
%   - backpropagation
%---

\chapterlesson{Activation Function}

\section{Nhu cầu}

Một neural network cần có khả năng biểu diễn các quan hệ phi tuyến.
Nếu tất cả layer chỉ thực hiện phép biến đổi tuyến tính, nhiều layer
kết hợp lại vẫn tương đương với một phép biến đổi tuyến tính duy nhất.

\section{Tại sao nhu cầu này xuất hiện?}

Các bài toán thực tế thường không thể được mô tả đầy đủ bằng một
đường thẳng hoặc một phép biến đổi tuyến tính đơn giản.

\section{Khái niệm cốt lõi}

Activation function là hàm được áp dụng lên đầu ra của neuron nhằm
tạo ra tính phi tuyến cho mạng neural.

\section{Kỹ thuật đang sử dụng}

\subsection{Cơ chế}

\begin{enumerate}
    \item Neuron nhận các giá trị đầu vào.
    \item Tính tổng có trọng số.
    \item Đưa kết quả qua activation function.
    \item Truyền đầu ra sang layer tiếp theo.
\end{enumerate}

\subsection{Các phương pháp phổ biến}

\begin{itemize}
    \item Sigmoid
    \item Tanh
    \item ReLU
    \item GELU
\end{itemize}

\section{Ví dụ ngắn}

Đưa ra một ví dụ có:

\begin{itemize}
    \item đầu vào;
    \item phép tính;
    \item đầu ra;
    \item ý nghĩa của kết quả.
\end{itemize}

\section{Ưu điểm}

\begin{itemize}
    \item Cho phép mô hình học quan hệ phi tuyến.
    \item Giúp mạng neural biểu diễn các hàm phức tạp.
\end{itemize}

\section{Hạn chế}

\begin{itemize}
    \item Một số hàm gây vanishing gradient.
    \item Việc lựa chọn không phù hợp có thể làm quá trình học kém ổn định.
\end{itemize}

\section{Khi nào sử dụng?}

Mô tả bối cảnh áp dụng và điều kiện sử dụng phù hợp.

\section{Liên kết kiến thức}

\begin{knowledgeconnections}
    \prerequisite{neural-network}
    \relatedtopic{loss-function}
    \relatedtopic{backpropagation}
\end{knowledgeconnections}

\section{Nhu cầu tiếp theo}

Activation function giúp mạng biểu diễn phi tuyến, nhưng chưa trả lời
được làm cách nào để biết dự đoán hiện tại đúng hay sai.

Do đó, nhu cầu tiếp theo là tìm hiểu:

\nexttopic{loss-function}

\section{Tóm tắt}

\begin{itemize}
    \item Activation function tạo tính phi tuyến.
    \item Nó được áp dụng sau phép tính tổng có trọng số.
    \item ReLU là một lựa chọn phổ biến trong nhiều mạng neural.
    \item Việc chọn activation ảnh hưởng đến quá trình huấn luyện.
\end{itemize}

\section{Tài liệu tham khảo}

\begin{itemize}
    \item Tên nguồn, tác giả, năm và URL.
\end{itemize}9. Phân biệt bài Overview và bài Deep DiveĐây là quy định rất quan trọng.Nếu không phân biệt, bài nền tảng sẽ ngày càng dài vì agent cố giải thích mọi nhánh phát sinh.Mỗi lesson cần có trường:depth: overviewhoặc:depth: standardhoặc:depth: deep-diveOverviewMục tiêu:giải thích bức tranh tổng thể;giới thiệu thuật ngữ;giải thích quan hệ giữa các thành phần;không đi sâu vào chi tiết kỹ thuật.Giới hạn đề xuất:1–3 trang
3–7 khái niệm chính
1 ví dụ tổng quát
không quá 2 công thứcStandardMục tiêu:hiểu cơ chế;biết cách áp dụng;hiểu ưu nhược điểm.Giới hạn đề xuất:3–7 trang
1–3 ví dụ
có thể có thuật toán hoặc công thứcDeep DiveMục tiêu:phân tích sâu;so sánh biến thể;giải thích trade-off;đề cập implementation và edge case.Không dùng bài deep-dive làm prerequisite bắt buộc cho người mới, trừ khi thực sự cần thiết.10. Chapter introMỗi chapter nên có một phần giới thiệu riêng thay vì đi thẳng vào lesson.Template chapter-intro.tex:\chapter{Tên chapter}

\begin{chapterobjective}
Sau chapter này, người đọc có thể:

\begin{itemize}
    \item Hiểu mục tiêu chính của chapter.
    \item Nhận diện các thành phần quan trọng.
    \item Biết các kiến thức sẽ được đào sâu ở chapter sau.
\end{itemize}
\end{chapterobjective}

\section*{Bối cảnh}

Giải thích chapter này xuất hiện sau chapter trước vì lý do gì.

\section*{Phạm vi}

Chapter này sẽ trình bày:

\begin{itemize}
    \item Nội dung A.
    \item Nội dung B.
\end{itemize}

Chapter này chưa đào sâu:

\begin{itemize}
    \item Nội dung C.
    \item Nội dung D.
\end{itemize}Learning path có thể chứa trực tiếp nội dung này:chapters:
  - id: neural-network-foundation

    title: "Nền tảng Neural Network"

    context: >
      Chapter trước đã giải thích Machine Learning và Deep Learning.
      Chapter này đi sâu vào cấu trúc cơ bản của Neural Network.

    objective:
      - Hiểu neuron và layer
      - Hiểu activation function
      - Hiểu loss và quá trình cập nhật trọng số

    out_of_scope:
      - Kiến trúc CNN chi tiết
      - Transformer
      - Distributed trainingScript sẽ sinh chapter intro tự động từ metadata này.11. Guideline cho agentFile guidelines/agent-instructions.md nên quy định rõ workflow.Nhiệm vụ của agentKhi thêm một chủ đề mới, agent phải:Xác định chủ đề có thực sự là một lesson độc lập không.Kiểm tra lesson tương tự đã tồn tại chưa.Xác định độ sâu của lesson.Xác định prerequisite thật sự.Xác định quan hệ trong graph.Xác định lesson thuộc learning path nào.Xác định chapter phù hợp.Không mặc định thêm bài vào cuối.Không tự đổi thứ tự hàng loạt nếu không cần.Chạy validation sau khi thay đổi.Quy tắc xác định prerequisiteMột lesson A chỉ là prerequisite của B khi:Người đọc không thể hiểu đúng B nếu chưa hiểu A.Không thêm prerequisite chỉ vì hai chủ đề có liên quan.Ví dụ:activation-function:
  prerequisites:
    - neural-networkHợp lý.Nhưng:activation-function:
  prerequisites:
    - transformerKhông hợp lý.Quy tắc chèn lesson vào learning pathAgent phải tìm:Bài gần nhất mà lesson mới phát triển từ đó
Bài gần nhất sử dụng lesson mới
Chapter có cùng learning objectiveSau đó chèn lesson vào giữa hai bài này.Ví dụ:Neural Network
Loss Function
BackpropagationThêm Activation Function:Neural Network
Activation Function
Loss Function
BackpropagationQuy tắc không làm lệch chapterNếu lesson mới là nhánh đào sâu nhưng không bắt buộc để tiếp tục mạch chính:thêm vào graph;thêm vào mục “đọc thêm”;không chèn vào core learning path.Ví dụ:chapters:
  - id: neural-network
    lessons:
      - neural-network
      - activation-function
      - loss-function
      - backpropagation

    optional_lessons:
      - activation-function-history
      - relu-variants
      - biological-neuron-comparison12. Core lesson và optional lessonĐể tránh chapter bị kéo dài vô hạn, mỗi chapter nên có hai danh sách.chapters:
  - id: neural-network

    title: "Neural Network"

    lessons:
      - neural-network
      - activation-function
      - loss-function
      - backpropagation

    optional_lessons:
      - sigmoid-vs-tanh
      - relu-variants
      - gradient-checkingPDF mặc định chỉ build lessons.Build đầy đủ:./build.sh artificial-intelligence foundation --include-optionalBuild ngắn:./build.sh artificial-intelligence foundationNhờ vậy, graph có thể tiếp tục phát triển nhưng learning path chính không bị phình to.13. Validation rulesScript validate.py cần kiểm tra các lỗi sau.Kiểm tra lessonID không được trùng.Tên file phải khớp ID.Metadata bắt buộc phải tồn tại.status phải hợp lệ.Prerequisite phải tồn tại.Related lesson phải tồn tại.Kiểm tra graphKhông tham chiếu node không tồn tại.Không có prerequisite cycle.Relation type phải nằm trong danh sách cho phép.Không khai báo hai relation trùng nhau.Kiểm tra learning pathLesson trong path phải tồn tại.Không có lesson trùng trong cùng path.Prerequisite bắt buộc phải xuất hiện trước lesson.Một lesson core không được phụ thuộc vào optional lesson.Chapter phải có objective.Overview không được phụ thuộc vào deep-dive.Không build lesson có trạng thái draft, trừ khi có flag cho phép.Ví dụ lỗi:Validation error:

Lesson: backpropagation
Missing prerequisite before lesson:
  gradient-descent

Path:
  artificial-intelligence/foundation

Chapter:
  neural-network-foundation14. Quy tắc statusMỗi lesson nên có trạng thái:status: draftCác giá trị hợp lệ:draft
review
complete
deprecatedÝ nghĩa:StatusÝ nghĩadraftĐang viếtreviewĐã đủ nội dung, cần kiểm tracompleteCó thể xuất bảndeprecatedKhông còn sử dụngMặc định build chỉ lấy:review
completeBuild cả draft:./build.sh artificial-intelligence foundation --include-draft15. Script buildGiao diện script:./build.sh <cookbook> [path] [options]Ví dụ:./build.sh artificial-intelligenceSử dụng default_path trong cookbook.yml../build.sh artificial-intelligence foundationBuild learning path foundation../build.sh artificial-intelligence completeBuild path đầy đủ../build.sh artificial-intelligence foundation --include-optionalThêm bài đọc mở rộng../build.sh artificial-intelligence foundation --validate-onlyChỉ kiểm tra, không tạo PDF.File build.sh#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COOKBOOK="${1:-}"
LEARNING_PATH="${2:-}"

if [ -z "$COOKBOOK" ]; then
    echo "Usage:"
    echo "  ./build.sh <cookbook> [learning-path] [options]"
    echo ""
    echo "Examples:"
    echo "  ./build.sh artificial-intelligence"
    echo "  ./build.sh artificial-intelligence foundation"
    echo "  ./build.sh artificial-intelligence complete --include-optional"
    exit 1
fi

shift || true

if [ -n "$LEARNING_PATH" ]; then
    shift || true
fi

python3 "$ROOT_DIR/scripts/build.py" \
    --cookbook "$COOKBOOK" \
    ${LEARNING_PATH:+--path "$LEARNING_PATH"} \
    "$@"16. Luồng xử lý của build.py1. Đọc cookbook.yml
2. Xác định learning path
3. Đọc path YAML
4. Đọc metadata tất cả lesson
5. Đọc graph.yml
6. Validate dependency
7. Validate chapter order
8. Lọc lesson theo status
9. Lọc optional lesson theo build flag
10. Sinh chapter intro
11. Sinh danh sách \input{}
12. Sinh file LaTeX tổng
13. Chạy latexmk
14. Xuất báo cáo buildPseudo-code:def build(cookbook_id, path_id, options):
    cookbook = load_cookbook(cookbook_id)
    learning_path = load_path(cookbook_id, path_id)
    graph = load_graph(cookbook_id)
    lessons = load_lessons(cookbook_id)

    validate_lessons(lessons)
    validate_graph(graph, lessons)
    validate_path(learning_path, graph, lessons)

    selected_lessons = resolve_path_lessons(
        learning_path,
        include_optional=options.include_optional,
        include_draft=options.include_draft,
    )

    latex = render_book(
        cookbook=cookbook,
        learning_path=learning_path,
        lessons=selected_lessons,
    )

    write_generated_tex(latex)

    if not options.validate_only:
        compile_pdf()17. Script tạo lesson mớiKhông nên tạo lesson bằng cách copy thủ công vì dễ quên metadata.Command:python3 scripts/create_lesson.py \
  artificial-intelligence \
  activation-function \
  --title "Activation Function" \
  --depth standard \
  --after neural-networkScript thực hiện:1. Kiểm tra ID chưa tồn tại.
2. Tạo file từ template.
3. Thêm node vào graph.yml.
4. Gợi ý relation.
5. Gợi ý chapter phù hợp.
6. Không tự sửa path nếu chưa đủ chắc chắn.Output:Created:
  src/artificial-intelligence/lessons/activation-function.tex

Added graph node:
  activation-function

Suggested placement:
  path: foundation
  chapter: neural-network-foundation
  after: neural-network

Next:
  Review graph relations and add the lesson to the path.Có thể thêm --apply khi muốn tự động chèn:python3 scripts/create_lesson.py \
  artificial-intelligence \
  activation-function \
  --title "Activation Function" \
  --after neural-network \
  --before loss-function \
  --apply18. Workflow thêm một chủ đề mớiBước 1: Phân loại chủ đềXác định:Đây là khái niệm nền tảng?
Một kỹ thuật?
Một thành phần?
Một ứng dụng?
Một nhánh đào sâu?Bước 2: Kiểm tra trùng lặpTìm trong:lesson ID
title
tags
graph relationsBước 3: Tạo lessonpython3 scripts/create_lesson.py \
  artificial-intelligence \
  activation-function \
  --title "Activation Function"Bước 4: Viết nội dung theo templateKhông bỏ qua:Nhu cầu
Nguyên nhân
Kỹ thuật
Ưu điểm
Hạn chế
Nhu cầu tiếp theoBước 5: Thêm graph relation- from: activation-function
  to: neural-network
  type: component_of

- from: activation-function
  to: loss-function
  type: related_toBước 6: Quyết định có đưa vào learning path khôngBa khả năng:Core
Optional
Graph-onlyCoreBắt buộc để theo mạch chính.OptionalCó giá trị nhưng không bắt buộc.Graph-onlyĐã lưu trong kho tri thức nhưng chưa thuộc path nào.Bước 7: Validate./build.sh artificial-intelligence foundation --validate-onlyBước 8: Build./build.sh artificial-intelligence foundation19. Nguyên tắc kiểm soát độ dài chapterMột chapter không nên cố giải quyết hết mọi vấn đề phát sinh.Quy tắc đề xuất:Tối đa 5–8 core lessons mỗi chapter.
Mỗi lesson chỉ có một mục tiêu chính.
Deep-dive chuyển thành optional lesson.
Nhánh phát sinh xa mục tiêu chapter chỉ được đưa vào graph.Khi chapter vượt quá giới hạn, agent phải chọn một trong ba cách:Tách thành chapter mới.Chuyển lesson sang optional.Chỉ lưu trong graph và đưa vào related topics.Ví dụ:Chapter: Neural Network Foundation

Core:
- Neural Network
- Neuron and Layer
- Activation Function
- Loss Function
- Backpropagation

Optional:
- Sigmoid History
- ReLU Variants
- Gradient Checking
- Biological Neuron Comparison20. Nguyên tắc nền tảngKiến trúc này dựa trên bốn quy tắc:Lesson là nội dung độc lập.
Graph phản ánh quan hệ tri thức.
Path phản ánh trải nghiệm học.
Chapter phản ánh mục tiêu nhận thức.Không để:Tên file quyết định thứ tự.
Graph tự quyết định toàn bộ PDF.
Một chapter giải quyết mọi nhánh phát sinh.
Một bài overview trở thành deep-dive.Mô hình tổng thể:                    ┌──────────────────┐
                    │ Knowledge Graph  │
                    │ Quan hệ tri thức │
                    └────────┬─────────┘
                             │ kiểm tra
                             ▼
┌──────────────┐     ┌──────────────────┐
│ Lesson Files │ ──► │  Learning Path   │
│ Nội dung     │     │  Thứ tự học      │
└──────────────┘     └────────┬─────────┘
                              │ build
                              ▼
                     ┌─────────────────┐
                     │ Cookbook PDF    │
                     │ Trải nghiệm đọc │
                     └─────────────────┘Kết quả là hệ thống vừa có thể mở rộng tự nhiên theo knowledge graph, vừa giữ được một cookbook tuyến tính, dễ học và có định hướng.
Cấu trúc cần thay đổi quan trọng nhất là tách graph.yml khỏi paths/*.yml. Script chỉ dùng graph để kiểm định learning path, không dùng graph để tự động viết thay cho người thiết kế chương trình học.
