local stringify = pandoc.utils.stringify

local section_classes = {
  ["Nhu cầu"] = "need",
  ["Tại sao có nhu cầu này?"] = "context",
  ["Khái niệm cốt lõi"] = "concept",
  ["Ví dụ"] = "example",
  ["Ưu điểm và hạn chế"] = "tradeoff",
  ["Khi nào nên và không nên dùng?"] = "tradeoff",
  ["Liên kết kiến thức"] = "connections",
  ["Nhu cầu tiếp theo"] = "next-step",
  ["Tóm tắt"] = "summary",
  ["Tài liệu tham khảo"] = "references",
}

local function append_blocks(target, source)
  for _, block in ipairs(source) do
    target:insert(block)
  end
end

local function section_content(blocks, start_index)
  local content = pandoc.Blocks({})
  local index = start_index + 1
  while index <= #blocks do
    local block = blocks[index]
    if block.t == "Header" and block.level <= 3 then
      break
    end
    content:insert(block)
    index = index + 1
  end
  return content, index
end

local function unwrap_matching_div(content, class_name)
  if #content == 1 and content[1].t == "Div"
      and content[1].classes:includes(class_name) then
    return content[1].content
  end
  return content
end

local function labelled_paragraph(label)
  return pandoc.Para({pandoc.Strong({pandoc.Str(label)})})
end

function Pandoc(document)
  local result = pandoc.Blocks({})
  local blocks = document.blocks
  local index = 1

  while index <= #blocks do
    local block = blocks[index]
    if block.t ~= "Header" or block.level ~= 3 then
      result:insert(block)
      index = index + 1
    else
      local title = stringify(block.content)
      local class_name = section_classes[title]
      local content, next_index = section_content(blocks, index)

      if title == "Nhu cầu" and next_index <= #blocks
          and blocks[next_index].t == "Header"
          and stringify(blocks[next_index].content) == "Tại sao có nhu cầu này?" then
        local context, after_context = section_content(blocks, next_index)
        content:insert(labelled_paragraph("Vì sao quan trọng?"))
        append_blocks(content, context)
        next_index = after_context
      elseif title == "Ưu điểm và hạn chế" and next_index <= #blocks
          and blocks[next_index].t == "Header"
          and stringify(blocks[next_index].content) == "Khi nào nên và không nên dùng?" then
        local decision, after_decision = section_content(blocks, next_index)
        content:insert(labelled_paragraph("Điều kiện áp dụng"))
        append_blocks(content, decision)
        next_index = after_decision
      end

      if class_name then
        content = unwrap_matching_div(content, class_name)
        result:insert(pandoc.Div(
          content,
          pandoc.Attr(block.identifier, {class_name, "editorial-card"})
        ))
      else
        block.classes:insert("editorial-section")
        result:insert(block)
        append_blocks(result, content)
      end
      index = next_index
    end
  end

  document.blocks = result
  return document
end
