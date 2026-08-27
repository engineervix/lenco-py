import { defineConfig } from "vitepress";
import llmstxt, { copyOrDownloadAsMarkdownButtons } from "vitepress-plugin-llms";

// GitHub Pages serves project sites under /<repo-name>/, so the base must
// match the repository the docs are deployed from. Locally (and for a
// custom domain or user/org page) this falls back to "/".
const base = process.env.GITHUB_ACTIONS
  ? `/${process.env.GITHUB_REPOSITORY?.split("/")[1] ?? ""}/`
  : "/";

export default defineConfig({
  title: "lenco-py",
  description: "Python SDK for the Lenco API v2",
  base,
  cleanUrls: true,
  srcExclude: ["**/_shared/**"],
  head: [["link", { rel: "icon", href: `${base}favicon.ico` }]],
  sitemap: {
    hostname: "https://engineervix.github.io/lenco-py/",
  },
  markdown: {
    config(md) {
      md.use(copyOrDownloadAsMarkdownButtons);
    },
  },
  vite: {
    plugins: [llmstxt()],
  },
  themeConfig: {
    search: {
      provider: "local",
    },
    externalLinkIcon: true,
    editLink: {
      pattern: "https://github.com/engineervix/lenco-py/edit/main/docs/:path",
      text: "Edit this page on GitHub",
    },
    lastUpdated: {
      text: "Last updated",
    },
    nav: [
      { text: "Guide", link: "/guide/getting-started" },
      { text: "Reference", link: "/reference/accounts" },
    ],
    sidebar: [
      {
        text: "Guide",
        items: [
          { text: "Getting started", link: "/guide/getting-started" },
          { text: "Handling webhooks", link: "/guide/webhooks" },
          { text: "Error handling", link: "/guide/errors" },
          { text: "Framework recipes", link: "/guide/frameworks" },
          { text: "Card collections", link: "/guide/card-collections" },
        ],
      },
      {
        text: "Reference",
        items: [
          { text: "Accounts", link: "/reference/accounts" },
          { text: "Banks", link: "/reference/banks" },
          { text: "Resolve", link: "/reference/resolve" },
          { text: "Transfer recipients", link: "/reference/transfer-recipients" },
          { text: "Transfers", link: "/reference/transfers" },
          { text: "Collections", link: "/reference/collections" },
          { text: "Settlements", link: "/reference/settlements" },
          { text: "Transactions", link: "/reference/transactions" },
        ],
      },
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/engineervix/lenco-py" }],
    footer: {
      message:
        'Built with <a href="https://vitepress.dev/">VitePress</a>. Not affiliated with Lenco.',
    },
  },
});
