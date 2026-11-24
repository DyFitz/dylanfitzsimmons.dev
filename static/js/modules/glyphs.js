// Half-width katakana and digits for the code rain, as in the films.
export const KATAKANA = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789";

// What text looks like while it's still being decrypted.
export const SCRAMBLE = "#$%&@*+=<>/|0123456789abcdefx";

export const randomGlyph = (glyphs) => glyphs.charAt(Math.floor(Math.random() * glyphs.length));

// Shows text decrypting: characters before `solved` are real, the rest are
// scrambled, and spaces always show as spaces.
export function scramble(text, solved) {
  let shown = "";
  for (let i = 0; i < text.length; i += 1) {
    const character = text.charAt(i);
    shown += i < solved || character === " " ? character : randomGlyph(SCRAMBLE);
  }
  return shown;
}
