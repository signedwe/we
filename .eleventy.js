module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/CNAME");

  eleventyConfig.addFilter("readable", (d) =>
    new Date(d).toLocaleDateString("en-GB", {
      day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
    })
  );
  eleventyConfig.addFilter("iso", (d) => new Date(d).toISOString());

  // Citations. Inside a post, a link becomes its own text followed by a small
  // numbered marker, and the number is the link. The prose reads clean; the
  // evidence is still one click away, in a new tab. Repeated sources keep the
  // same number. Nothing outside <article> is touched, so the masthead, the
  // footer and the index are left alone.
  eleventyConfig.addTransform("citations", function (content, outputPath) {
    const out = outputPath || (this.page && this.page.outputPath) || "";
    if (!String(out).endsWith(".html")) return content;

    return content.replace(/<article[\s\S]*?<\/article>/, (article) => {
      const numbers = new Map();
      return article.replace(
        /<a href="(https?:\/\/[^"]+)"[^>]*>([\s\S]*?)<\/a>/g,
        (_whole, url, text) => {
          if (!numbers.has(url)) numbers.set(url, numbers.size + 1);
          const n = numbers.get(url);
          return (
            text +
            '<a class="ref" href="' + url + '"' +
            ' target="_blank" rel="noopener noreferrer"' +
            ' aria-label="Source ' + n + ', opens in a new tab">' + n + "</a>"
          );
        }
      );
    });
  });

  eleventyConfig.addCollection("posts", (c) =>
    c.getFilteredByGlob("src/posts/*.md").reverse()
  );

  return {
    // The site lives in a subfolder on GitHub Pages, so every internal
    // path needs this on the front of it. Templates go through the
    // `url` filter; the plugin catches anything that doesn't.
    pathPrefix: "/we/",
    dir: { input: "src", output: "_site", includes: "_includes" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};
