import React from "react";

const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  // Функция для обработки текста с базовым форматированием
  const formatText = (text) => {
    if (!text) return "";

    return text.split("\n").map((line, index) => {
      let formattedLine = line;

      // Заголовки уровня 1 (##)
      if (line.startsWith("## ")) {
        return (
          <h2 key={index} className="markdown-h2">
            {line.replace("## ", "")}
          </h2>
        );
      }

      // Заголовки уровня 2 (###)
      if (line.startsWith("### ")) {
        return (
          <h3 key={index} className="markdown-h3">
            {line.replace("### ", "")}
          </h3>
        );
      }

      // Жирный текст (**текст**)
      formattedLine = formattedLine.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>",
      );

      // Курсив (*текст*)
      formattedLine = formattedLine.replace(/\*(.*?)\*/g, "<em>$1</em>");

      // Блочные цитаты (> текст)
      if (line.startsWith("> ")) {
        return (
          <blockquote key={index} className="markdown-blockquote">
            {line.replace("> ", "")}
          </blockquote>
        );
      }

      // Маркированные списки (- элемент)
      if (line.startsWith("- ")) {
        return (
          <li key={index} className="markdown-li">
            • {line.replace("- ", "")}
          </li>
        );
      }

      // Нумерованные списки (1. элемент)
      if (/^\d+\.\s/.test(line)) {
        return (
          <li key={index} className="markdown-li">
            {line}
          </li>
        );
      }

      // Пустые строки
      if (line.trim() === "") {
        return <br key={index} />;
      }

      // Обычные параграфы
      return (
        <p
          key={index}
          className="markdown-paragraph"
          dangerouslySetInnerHTML={{ __html: formattedLine }}
        />
      );
    });
  };

  return <div className="markdown-container">{formatText(content)}</div>;
};

export default MarkdownRenderer;
