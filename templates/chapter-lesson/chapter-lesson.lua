local chapter_number = 0
local lesson_number = 0

local function prepend_label(header, label, class_name, separator)
  local content = pandoc.Inlines({
    pandoc.Span(label, pandoc.Attr("", {class_name})),
    pandoc.Space(),
    pandoc.Str(separator),
    pandoc.Space(),
  })
  content:extend(header.content)
  header.content = content
  return header
end

function Header(header)
  if header.level == 1 then
    chapter_number = chapter_number + 1
    lesson_number = 0
    return prepend_label(
      header,
      string.format("CHƯƠNG %02d", chapter_number),
      "chapter-index",
      "·"
    )
  end
  if header.level == 2 then
    lesson_number = lesson_number + 1
    return prepend_label(
      header,
      string.format("Bài %02d", lesson_number),
      "lesson-index",
      "—"
    )
  end
  return header
end
