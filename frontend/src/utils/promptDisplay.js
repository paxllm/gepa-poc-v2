const EVALUATION_FOCUS_MARKER = '## Evaluation Focus (Talent Lens)';
const COMPOSED_PROMPT_FOOTER = '\n\nEvaluate the candidate against';

export function isComposedPrompt(text) {
  return text.trim().startsWith('## Job Description');
}

export function extractUserLens(text) {
  const stripped = text.trim();
  if (!isComposedPrompt(stripped)) {
    return stripped;
  }

  const idx = stripped.indexOf(EVALUATION_FOCUS_MARKER);
  if (idx === -1) {
    return stripped;
  }

  let lens = stripped.slice(idx + EVALUATION_FOCUS_MARKER.length).replace(/^\n/, '');
  const footerIdx = lens.indexOf(COMPOSED_PROMPT_FOOTER);
  if (footerIdx !== -1) {
    lens = lens.slice(0, footerIdx);
  }
  return lens.trim();
}

export function displayPromptText(text) {
  if (text == null || text === '') return '';
  return extractUserLens(text);
}
