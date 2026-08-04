local labels = {
  ["chapter-objective"] = "Mục tiêu chương",
  ["need"] = "Vấn đề cần giải quyết",
  ["context"] = "Vì sao quan trọng?",
  ["concept"] = "Khái niệm cốt lõi",
  ["example"] = "Ví dụ",
  ["tradeoff"] = "Quyết định và giới hạn",
  ["connections"] = "Liên kết kiến thức",
  ["summary"] = "Ghi nhớ",
  ["references"] = "Tài liệu tham khảo",
  ["warning"] = "Cảnh báo",
  ["next-step"] = "Nhu cầu tiếp theo",
}

local latex_environments = {
  ["chapter-objective"] = "chapterobjectivebox",
  ["need"] = "needbox",
  ["context"] = "contextbox",
  ["concept"] = "conceptbox",
  ["example"] = "examplebox",
  ["tradeoff"] = "tradeoffbox",
  ["connections"] = "connectionsbox",
  ["summary"] = "summarybox",
  ["references"] = "referencesbox",
  ["warning"] = "warningbox",
  ["next-step"] = "nextstepbox",
}

function Div(element)
  local kind = nil
  for class_name, _ in pairs(labels) do
    if element.classes:includes(class_name) then
      kind = class_name
      break
    end
  end
  if not kind then
    return nil
  end

  if FORMAT:match("latex") then
    local environment = latex_environments[kind]
    table.insert(element.content, 1, pandoc.RawBlock("latex", "\\begin{" .. environment .. "}"))
    table.insert(element.content, pandoc.RawBlock("latex", "\\end{" .. environment .. "}"))
    return element.content
  end

  if FORMAT:match("html") then
    element.classes:insert("admonition")
    table.insert(element.content, 1, pandoc.Para({
      pandoc.Strong({pandoc.Str(labels[kind])})
    }))
    return element
  end

  return element
end
