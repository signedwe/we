module.exports = function (eleventyConfig) {
  // The scoreboard lives with the agent, because the agent writes it. The
  // site reads it. Nobody edits it by hand.
  eleventyConfig.addGlobalData("predictions", () => {
    const fs = require("fs");
    const path = require("path");
    const file = path.join(__dirname, "agent", "predictions.json");
    try {
      return JSON.parse(fs.readFileSync(file, "utf-8"));
    } catch (e) {
      return [];
    }
  });

  eleventyConfig.addFilter("byStatus", (rows, status) =>
    (rows || []).filter((r) => r.status === status)
  );

  eleventyConfig.addPassthroughCopy("src/css");
  // Files served as-is at the site root (search engine verification).
  eleventyConfig.addPassthroughCopy({ "src/static": "/" });

  // Which kind page a post belongs to, from its form (or Breaking).
  const KIND = { five_years: "five-years", response: "responses", top_ten: "top-tens",
    technical: "how-it-works", fiction: "serial", how_to: "how-to", obituary: "obituaries",
    learnt: "learnt" };
  eleventyConfig.addFilter("kindslug", (form, provenance) =>
    KIND[form] || (provenance === "conversation" ? "breaking" : (form ? "" : "responses")));

  eleventyConfig.addFilter("readable", (d) =>
    new Date(d).toLocaleDateString("en-GB", {
      day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
    })
  );
  eleventyConfig.addFilter("iso", (d) => new Date(d).toISOString());
  // The social card for a page: /posts/x/ -> cards/posts-x.png (scripts/cards.py uses the same rule).
  eleventyConfig.addFilter("cardname", (u) => (u || "").replace(/^\/+|\/+$/g, "").replace(/\//g, "-") || "home");

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

  eleventyConfig.addCollection("breaking", (c) =>
    c.getFilteredByGlob("src/posts/*.md")
      .filter((p) => p.data.provenance === "conversation")
      .reverse()
  );

  // Kinds of post, one collection each, for the Topics page. A post with no
  // form key is a response from before the rota existed (19 September 2026).
  const byForm = (form) => (c) =>
    c.getFilteredByGlob("src/posts/*.md").filter((p) => p.data.form === form).reverse();
  eleventyConfig.addCollection("kind_responses", (c) =>
    c.getFilteredByGlob("src/posts/*.md")
      .filter((p) => (p.data.form === "response" || !p.data.form) && p.data.provenance !== "conversation")
      .reverse()
  );
  eleventyConfig.addCollection("kind_five-years", byForm("five_years"));
  eleventyConfig.addCollection("kind_top-tens", byForm("top_ten"));
  eleventyConfig.addCollection("kind_how-it-works", byForm("technical"));
  eleventyConfig.addCollection("kind_serial", byForm("fiction"));
  eleventyConfig.addCollection("kind_how-to", byForm("how_to"));
  eleventyConfig.addCollection("kind_obituaries", byForm("obituary"));
  eleventyConfig.addCollection("kind_learnt", byForm("learnt"));
  eleventyConfig.addCollection("kind_breaking", (c) =>
    c.getFilteredByGlob("src/posts/*.md").filter((p) => p.data.provenance === "conversation").reverse()
  );
  eleventyConfig.addCollection("kind_ideas", (c) =>
    c.getFilteredByGlob("src/ideas/*.md").reverse()
  );

  eleventyConfig.addCollection("ideas", (c) =>
    c.getFilteredByGlob("src/ideas/*.md").reverse()
  );

  // Three other pages that share the most topics with this one, newest first.
  eleventyConfig.addFilter("related", (tags, url, all) => {
    const mine = new Set((tags || []).filter((t) => t !== "posts" && t !== "ideas"));
    if (!mine.size) return [];
    return (all || [])
      .filter((p) => p.url !== url)
      .map((p) => ({ p, n: (p.data.tags || []).filter((t) => mine.has(t)).length }))
      .filter((x) => x.n > 0)
      .sort((a, b) => b.n - a.n || b.p.date - a.p.date)
      .slice(0, 3)
      .map((x) => x.p);
  });

  eleventyConfig.addCollection("everything", (c) =>
    c.getFilteredByGlob(["src/posts/*.md", "src/ideas/*.md"])
  );

  // The Friday serial, oldest first, so the page reads as one story.
  eleventyConfig.addCollection("serial", (c) =>
    c.getFilteredByGlob("src/posts/*.md").filter((p) => p.data.form === "fiction")
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
