#!/usr/bin/env node

const http = require("http");
const WebSocket = require("ws");

const DEFAULT_PORT = Number(process.env.SSHCFG_CDP_PORT || 9222);
const DEFAULT_TARGET_HINT = process.env.SSHCFG_TARGET_HINT || "index.html#/";

function httpGetJson(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(new Error(`Failed to parse JSON from ${url}: ${error.message}`));
        }
      });
    });
    req.on("error", reject);
  });
}

async function getPageTarget(port) {
  const targets = await httpGetJson(`http://127.0.0.1:${port}/json/list`);
  const target = targets.find(
    (item) =>
      item.type === "page" &&
      typeof item.url === "string" &&
      item.url.includes(DEFAULT_TARGET_HINT),
  );
  if (!target) {
    throw new Error(
      `No page target matching "${DEFAULT_TARGET_HINT}" on port ${port}.`,
    );
  }
  return target;
}

class CdpClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.pending = new Map();
  }

  async connect() {
    await new Promise((resolve, reject) => {
      this.ws.once("open", resolve);
      this.ws.once("error", reject);
    });

    this.ws.on("message", (data) => {
      const msg = JSON.parse(data.toString());
      if (!Object.prototype.hasOwnProperty.call(msg, "id")) return;
      const pending = this.pending.get(msg.id);
      if (!pending) return;
      this.pending.delete(msg.id);
      if (msg.error) pending.reject(new Error(msg.error.message));
      else pending.resolve(msg.result);
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }), (error) => {
        if (error) {
          this.pending.delete(id);
          reject(error);
        }
      });
    });
  }

  async evaluate(expression, { awaitPromise = false } = {}) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise,
    });
    if (result.exceptionDetails) {
      throw new Error("Runtime.evaluate returned exception details.");
    }
    return result.result.value;
  }

  close() {
    this.ws.close();
  }
}

function jsString(value) {
  return JSON.stringify(String(value));
}

function printJson(value) {
  console.log(JSON.stringify(value, null, 2));
}

const SAFE_ACTIONS = {
  "system.datetime.request-date-time": {
    route: "/system-settings/datetime",
    risk: "safe-read",
    command: "date_time",
    trigger: { type: "text", value: "Запросить", nth: 0 },
    collect: "snapshot",
  },
  "system.datetime.request-timezone": {
    route: "/system-settings/datetime",
    risk: "safe-read",
    command: "timezone",
    trigger: { type: "text", value: "Запросить", nth: 1 },
    collect: "snapshot",
  },
  "system.kernel.request-cpu-qty": {
    route: "/system-settings/kernel-isolation",
    risk: "safe-read",
    command: "get_cpu_qty",
    trigger: { type: "text", value: "Запросить", nth: 0 },
    collect: "snapshot",
  },
  "system.host.request-type": {
    route: "/system-settings/system-commands",
    risk: "safe-read",
    command: "check_host_type",
    trigger: { type: "text", value: "Запросить", nth: 0 },
    collect: "snapshot",
  },
  "network.settings.reload-details": {
    route: "/network-settings/settings",
    risk: "safe-read",
    command: "get_interface_details",
    trigger: { type: "accordion-index", accordion: "Сетевые настройки", value: 0 },
    collect: "tables",
  },
  "network.files.list": {
    route: "/network-settings/files",
    risk: "safe-read",
    command: "list_files_by_directory network",
    trigger: { type: "accordion-index", accordion: "Список файлов сетевой конфигурации", value: 0 },
    collect: "tables",
  },
  "keys.list-user-keys": {
    route: "/keys",
    risk: "safe-read",
    command: "list_user_keys",
    trigger: { type: "text", value: "Вывести список ключей", nth: 0 },
    collect: "tables",
  },
  "diagnostics.check-systemd-journald": {
    route: "/diagnostics",
    risk: "safe-read",
    command: "check_status systemd-journald",
    prepare: { type: "diagnostics-service", value: "systemd-journald" },
    trigger: { type: "text", value: "Выполнить", nth: 0 },
    collect: "snapshot",
  },
  "vm.management.list": {
    route: "/manage/vm/management",
    risk: "safe-read",
    command: "list_vms",
    trigger: { type: "title", value: "Вывести список" },
    collect: "tables",
  },
  "vm.xmls.list": {
    route: "/manage/vm/xmls",
    risk: "safe-read",
    command: "list_files_by_directory xml",
    trigger: { type: "text", value: "Вывести список", nth: 0 },
    collect: "tables",
  },
  "vm.images.list": {
    route: "/manage/vm/images",
    risk: "safe-read",
    command: "list_files_by_directory images",
    trigger: { type: "text", value: "Вывести список", nth: 0 },
    collect: "tables",
  },
  "vm.grouped-files.list": {
    route: "/manage/vm/grouped-files",
    risk: "safe-read",
    command: "group_files_by_type_and_vm",
    trigger: { type: "text", value: "Вывести список", nth: 0 },
    collect: "tables",
  },
  "vm.pci.list": {
    route: "/manage/vm/pci-devices",
    risk: "safe-read",
    command: "list_pci_devices_by_iommu_group",
    trigger: { type: "text", value: "Вывести список", nth: 0 },
    collect: "tables",
  },
};

async function withClient(fn) {
  const target = await getPageTarget(DEFAULT_PORT);
  const client = new CdpClient(target.webSocketDebuggerUrl);
  await client.connect();

  try {
    return await fn(client);
  } finally {
    client.close();
  }
}

async function listElements(client) {
  return client.evaluate(`(() => {
    const els = [...document.querySelectorAll('input, textarea, select, button')];
    return els.map((el, i) => ({
      i,
      tag: el.tagName,
      id: el.id || '',
      type: el.type || '',
      value: 'value' in el ? el.value : '',
      text: (el.innerText || el.textContent || '').trim().slice(0, 80),
      title: el.getAttribute('title') || '',
      disabled: Boolean(el.disabled),
      cls: (el.className || '').toString().slice(0, 120)
    }));
  })()`);
}

async function gotoRoute(client, route) {
  const normalizedRoute = route.startsWith("/") ? route : `/${route}`;
  return client.evaluate(`(() => new Promise(async (resolve) => {
    location.hash = ${jsString(`#${normalizedRoute}`)};
    await new Promise((r) => setTimeout(r, 400));
    resolve({
      route: location.hash,
      title: document.title,
      statusText: document.body.innerText.includes('Статус: подключен') ? 'connected' : (
        document.body.innerText.includes('Статус: отключен') ? 'disconnected' : 'unknown'
      )
    });
  }))()`, { awaitPromise: true });
}

async function snapshot(client) {
  return client.evaluate(`(() => ({
    route: location.hash,
    buttons: [...document.querySelectorAll('button')].map((el) => ({
      text: (el.innerText || el.textContent || '').trim(),
      title: el.getAttribute('title') || '',
      disabled: Boolean(el.disabled)
    })).filter((item) => item.text || item.title),
    inputs: [...document.querySelectorAll('input, textarea, select')].map((el) => ({
      tag: el.tagName,
      type: el.type || '',
      id: el.id || '',
      value: 'value' in el ? String(el.value).slice(0, 120) : '',
      placeholder: el.placeholder || ''
    })),
    headings: [...document.querySelectorAll('h1,h2,h3,.p-accordion-header-text,.tab-btn,.menu-item span')]
      .map((el) => (el.innerText || el.textContent || '').trim())
      .filter(Boolean),
    body: document.body.innerText.slice(0, 1500)
  }))()`);
}

async function readTables(client) {
  return client.evaluate(`(() => {
    const tables = [...document.querySelectorAll('table')].map((table, index) => {
      const rows = [...table.querySelectorAll('tr')].map((tr) =>
        [...tr.querySelectorAll('th,td')].map((cell) => (cell.innerText || cell.textContent || '').trim())
      ).filter((row) => row.some(Boolean));
      return { index, rows };
    }).filter((table) => table.rows.length > 0);

    const textareas = [...document.querySelectorAll('textarea')].map((el, index) => ({
      index,
      value: String(el.value || '').slice(0, 2000),
    })).filter((item) => item.value);

    return {
      route: location.hash,
      tables,
      textareas,
    };
  })()`);
}

async function readSelections(client) {
  return client.evaluate(`(() => {
    const appTables = [...document.querySelectorAll('.table-widget')].map((table, tableIndex) => {
      const selectedRow = table.querySelector('tr.selected');
      const selected = selectedRow
        ? [...selectedRow.querySelectorAll('td')].map((cell) => (cell.innerText || cell.textContent || '').trim())
        : null;
      return { tableIndex, selected };
    });

    const primeTables = [...document.querySelectorAll('.p-datatable')].map((table, tableIndex) => {
      const selectedRow = table.querySelector('tbody tr.p-datatable-row-selected, tbody tr[aria-selected="true"]');
      const selected = selectedRow
        ? [...selectedRow.querySelectorAll('td')].map((cell) => (cell.innerText || cell.textContent || '').trim())
        : null;
      return { tableIndex, selected };
    });

    const enabledButtons = [...document.querySelectorAll('button')]
      .map((el, i) => ({
        i,
        text: (el.innerText || el.textContent || '').trim(),
        title: el.getAttribute('title') || '',
        disabled: Boolean(el.disabled)
      }))
      .filter((item) => item.text || item.title);

    const textInputs = [...document.querySelectorAll('input[type="text"], textarea')].map((el, i) => ({
      i,
      value: String(el.value || ''),
      cls: (el.className || '').toString()
    }));

    return {
      route: location.hash,
      appTables,
      primeTables,
      enabledButtons,
      textInputs
    };
  })()`);
}

async function readNetworkFilesState(client) {
  return client.evaluate(`(() => {
    const rows = [...document.querySelectorAll('.table-widget tbody tr')]
      .map((tr) => [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim()));
    const selectedRow = document.querySelector('.table-widget tbody tr.selected');
    const renameInput = document.querySelector('article.page-content input[type="text"]');
    const renameButton = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Переименовать') || null;
    const iconButtons = [...document.querySelectorAll('.accordion .content button.btn')]
      .map((el, i) => ({
        i,
        text: (el.innerText || el.textContent || '').trim(),
        title: el.getAttribute('title') || '',
        disabled: Boolean(el.disabled),
        cls: (el.className || '').toString()
      }));
    return {
      route: location.hash,
      rows,
      selected: selectedRow
        ? [...selectedRow.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim())
        : null,
      renameTarget: renameInput ? String(renameInput.value || '') : null,
      renameEnabled: renameButton ? !renameButton.disabled : null,
      iconButtons
    };
  })()`);
}

async function readVmFileListState(client, kind) {
  const headerText = kind === "xml" ? "XML file" : "Image file";
  return client.evaluate(`(() => {
    const headerText = ${jsString(headerText)};
    const table = [...document.querySelectorAll('.p-datatable')]
      .find((el) => (el.innerText || el.textContent || '').includes(headerText)) || document.querySelector('.p-datatable');
    const rows = table
      ? [...table.querySelectorAll('tbody tr')].map((tr) =>
          [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim())
        ).filter((row) => row.some(Boolean))
      : [];
    const selectedRow = table ? table.querySelector('tbody tr.p-datatable-row-selected, tbody tr[aria-selected="true"]') : null;
    const renameInput = document.querySelector('article.page-content input[type="text"]');
    const renameButton = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Переименовать') || null;
    const deleteButton = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Удалить') || null;
    return {
      route: location.hash,
      headerText,
      rows,
      selected: selectedRow
        ? [...selectedRow.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim())
        : null,
      renameTarget: renameInput ? String(renameInput.value || '') : null,
      renameEnabled: renameButton ? !renameButton.disabled : null,
      deleteEnabled: deleteButton ? !deleteButton.disabled : null
    };
  })()`);
}

async function readKeysState(client) {
  return client.evaluate(`(() => {
    const table = document.querySelector('.p-datatable');
    const rows = table
      ? [...table.querySelectorAll('tbody tr')].map((tr, i) => ({
          i,
          text: (tr.innerText || tr.textContent || '').trim(),
          ariaSelected: tr.getAttribute('aria-selected'),
          cls: tr.className
        }))
      : [];
    const deleteButton = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Удалить ключ') || null;
    return {
      route: location.hash,
      rowCount: rows.length,
      rows,
      deleteEnabled: deleteButton ? !deleteButton.disabled : null
    };
  })()`);
}

async function selectAppTableRow(client, rowText, tableIndex = 0) {
  return client.evaluate(`(() => {
    const fireClick = (el) => {
      for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
        el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
      }
    };
    const rowText = ${jsString(rowText)};
    const tableIndex = ${Number(tableIndex)};
    const tables = [...document.querySelectorAll('.table-widget')];
    const table = tables[tableIndex] || null;
    if (!table) {
      return { ok: false, reason: 'app table not found', tableIndex, count: tables.length };
    }
    const rows = [...table.querySelectorAll('tbody tr')];
    const row = rows.find((tr) => {
      const text = [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim()).join(' | ');
      return text.includes(rowText);
    }) || null;
    if (!row) {
      return {
        ok: false,
        reason: 'row not found',
        tableIndex,
        rowText,
        rows: rows.map((tr) => [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim()))
      };
    }
    fireClick(row);
    return {
      ok: true,
      tableIndex,
      rowText,
      selected: [...row.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim())
    };
  })()`);
}

async function selectPrimeTableRow(client, rowText, tableIndex = 0) {
  return client.evaluate(`(() => {
    const fireClick = (el) => {
      for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
        el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
      }
    };
    const rowText = ${jsString(rowText)};
    const tableIndex = ${Number(tableIndex)};
    const tables = [...document.querySelectorAll('.p-datatable')];
    const table = tables[tableIndex] || null;
    if (!table) {
      return { ok: false, reason: 'prime table not found', tableIndex, count: tables.length };
    }
    const rows = [...table.querySelectorAll('tbody tr')];
    const row = rows.find((tr) => {
      const text = [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim()).join(' | ');
      return text.includes(rowText);
    }) || null;
    if (!row) {
      return {
        ok: false,
        reason: 'row not found',
        tableIndex,
        rowText,
        rows: rows.map((tr) => [...tr.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim()))
      };
    }
    fireClick(row);
    return {
      ok: true,
      tableIndex,
      rowText,
      selected: [...row.querySelectorAll('td')].map((td) => (td.innerText || td.textContent || '').trim())
    };
  })()`);
}

async function selectNetworkFile(client, fileName) {
  const { connectResult, closeSettingsResult } = await ensureConnectedAndClean(client);
  const routeState = await gotoRoute(client, "/network-settings/files");
  const listResult = await runSafeAction(client, "network.files.list");
  const selectResult = await selectAppTableRow(client, fileName, 0);
  await sleep(client, 150);
  const state = await readNetworkFilesState(client);
  return {
    ok: Boolean(selectResult?.ok) && state.renameTarget === fileName && state.renameEnabled === true,
    route: routeState.route,
    connectResult,
    closeSettingsResult,
    listResult: {
      ok: listResult.ok,
      matchedCommand: listResult.matchedCommand,
      rows: listResult.state?.tables?.[0]?.rows || []
    },
    selectResult,
    state
  };
}

async function setNetworkFileRenameTarget(client, newName) {
  return client.evaluate(`(() => {
    const input = document.querySelector('article.page-content input[type="text"]');
    if (!input) {
      return { ok: false, reason: 'rename input not found' };
    }
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, ${jsString(newName)});
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    const renameButton = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Переименовать') || null;
    return {
      ok: true,
      value: String(input.value || ''),
      renameEnabled: renameButton ? !renameButton.disabled : null
    };
  })()`);
}

async function prepareNetworkFileRename(client, fileName, newName) {
  const selectResult = await selectNetworkFile(client, fileName);
  if (!selectResult.ok) {
    return {
      ok: false,
      reason: 'select-network-file failed',
      selectResult
    };
  }
  const renameTargetResult = await setNetworkFileRenameTarget(client, newName);
  await sleep(client, 150);
  const state = await readNetworkFilesState(client);
  return {
    ok: Boolean(renameTargetResult?.ok) && state.renameTarget === newName && state.renameEnabled === true,
    route: state.route,
    selectResult,
    renameTargetResult,
    state
  };
}

async function selectFirstKey(client) {
  const { connectResult, closeSettingsResult } = await ensureConnectedAndClean(client);
  const routeState = await gotoRoute(client, "/keys");
  const listResult = await runSafeAction(client, "keys.list-user-keys");
  const selectResult = await client.evaluate(`(() => {
    const fireClick = (el) => {
      for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
        el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
      }
    };
    const row = document.querySelector('.p-datatable tbody tr');
    if (!row) {
      return { ok: false, reason: 'first key row not found' };
    }
    fireClick(row);
    return {
      ok: true,
      ariaSelected: row.getAttribute('aria-selected'),
      cls: row.className
    };
  })()`);
  await sleep(client, 200);
  const state = await readKeysState(client);
  return {
    ok: Boolean(selectResult?.ok) && state.deleteEnabled === true,
    route: routeState.route,
    connectResult,
    closeSettingsResult,
    listResult: {
      ok: listResult.ok,
      matchedCommand: listResult.matchedCommand,
      matchedItem: listResult.matchedItem || null
    },
    selectResult,
    state
  };
}

async function deleteSelectedKey(client) {
  return client.evaluate(`(() => {
    const button = [...document.querySelectorAll('article.page-content button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Удалить ключ') || null;
    if (!button) {
      return { ok: false, reason: 'delete key button not found' };
    }
    if (button.disabled) {
      return { ok: false, reason: 'delete key button is disabled' };
    }
    for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
      button.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    return { ok: true, text: (button.innerText || button.textContent || '').trim() };
  })()`);
}

async function selectVmXmlFile(client, fileName) {
  const { connectResult, closeSettingsResult } = await ensureConnectedAndClean(client);
  const routeState = await gotoRoute(client, "/manage/vm/xmls");
  const listResult = await runSafeAction(client, "vm.xmls.list");
  const selectResult = await selectPrimeTableRow(client, fileName, 0);
  await sleep(client, 150);
  const state = await readVmFileListState(client, "xml");
  return {
    ok: Boolean(selectResult?.ok) && state.renameTarget === fileName && state.renameEnabled === true,
    route: routeState.route,
    connectResult,
    closeSettingsResult,
    listResult: {
      ok: listResult.ok,
      matchedCommand: listResult.matchedCommand,
      rows: listResult.state?.tables?.[0]?.rows || [],
      matchedItem: listResult.matchedItem || null
    },
    selectResult,
    state
  };
}

async function selectVmImageFile(client, fileName) {
  const { connectResult, closeSettingsResult } = await ensureConnectedAndClean(client);
  const routeState = await gotoRoute(client, "/manage/vm/images");
  const listResult = await runSafeAction(client, "vm.images.list");
  const selectResult = await selectPrimeTableRow(client, fileName, 0);
  await sleep(client, 150);
  const state = await readVmFileListState(client, "images");
  return {
    ok: Boolean(selectResult?.ok) && state.renameTarget === fileName && state.renameEnabled === true,
    route: routeState.route,
    connectResult,
    closeSettingsResult,
    listResult: {
      ok: listResult.ok,
      matchedCommand: listResult.matchedCommand,
      rows: listResult.state?.tables?.[0]?.rows || [],
      matchedItem: listResult.matchedItem || null
    },
    selectResult,
    state
  };
}

async function setHost(client, host) {
  return client.evaluate(`(() => {
    const el = document.querySelector('#host-input');
    if (!el) return { ok: false, reason: 'host-input not found' };
    el.focus();
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      'value'
    ).set;
    setter.call(el, ${jsString(host)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return { ok: true, value: el.value };
  })()`);
}

async function clickText(client, buttonText) {
  return client.evaluate(`(() => {
    const text = ${jsString(buttonText)};
    const button = [...document.querySelectorAll('button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === text);
    if (!button) return { ok: false, reason: 'button not found', text };
    button.click();
    return { ok: true, text };
  })()`);
}

async function clickTextNth(client, buttonText, nth = 0) {
  return client.evaluate(`(() => {
    const text = ${jsString(buttonText)};
    const nth = ${Number(nth)};
    const buttons = [...document.querySelectorAll('button')]
      .filter((el) => (el.innerText || el.textContent || '').trim() === text);
    const button = buttons[nth] || null;
    if (!button) return { ok: false, reason: 'button not found', text, nth, matches: buttons.length };
    button.click();
    return { ok: true, text, nth, matches: buttons.length };
  })()`);
}

async function clickTitle(client, titleText) {
  return client.evaluate(`(() => {
    const title = ${jsString(titleText)};
    const button = [...document.querySelectorAll('button')]
      .find((el) => (el.getAttribute('title') || '').trim() === title);
    if (!button) return { ok: false, reason: 'button not found', title };
    button.click();
    return { ok: true, title };
  })()`);
}

async function clickButtonIndex(client, index) {
  return client.evaluate(`(() => {
    const index = ${Number(index)};
    const buttons = [...document.querySelectorAll('button')];
    const button = buttons[index] || null;
    if (!button) return {
      ok: false,
      reason: 'button not found',
      index,
      count: buttons.length,
      buttons: buttons.map((el, i) => ({
        i,
        text: (el.innerText || el.textContent || '').trim(),
        title: el.getAttribute('title') || '',
        disabled: Boolean(el.disabled)
      }))
    };
    button.click();
    return {
      ok: true,
      index,
      text: (button.innerText || button.textContent || '').trim(),
      title: button.getAttribute('title') || ''
    };
  })()`);
}

async function clickPageButtonIndex(client, index) {
  return client.evaluate(`(() => {
    const index = ${Number(index)};
    const scope = document.querySelector('article.page-content') || document.body;
    const buttons = [...scope.querySelectorAll('button')];
    const button = buttons[index] || null;
    if (!button) return {
      ok: false,
      reason: 'button not found',
      index,
      count: buttons.length,
      buttons: buttons.map((el, i) => ({
        i,
        text: (el.innerText || el.textContent || '').trim(),
        title: el.getAttribute('title') || '',
        disabled: Boolean(el.disabled)
      }))
    };
    button.click();
    return {
      ok: true,
      index,
      text: (button.innerText || button.textContent || '').trim(),
      title: button.getAttribute('title') || ''
    };
  })()`);
}

async function clickAccordionButtonIndex(client, accordionHeader, index) {
  return client.evaluate(`(() => {
    const headerText = ${jsString(accordionHeader)};
    const index = ${Number(index)};
    const sections = [...document.querySelectorAll('.accordion')];
    const section = sections.find((el) => {
      const header = el.querySelector('.header');
      const text = (header?.innerText || header?.textContent || '').trim().replace(/\\s+/g, ' ');
      return text.includes(headerText);
    }) || null;
    if (!section) {
      return { ok: false, reason: 'accordion not found', headerText };
    }
    const content = section.querySelector('.content');
    if (!content) {
      return { ok: false, reason: 'accordion content not visible', headerText };
    }
    const buttons = [...content.querySelectorAll('button')];
    const button = buttons[index] || null;
    if (!button) {
      return {
        ok: false,
        reason: 'button not found',
        headerText,
        index,
        count: buttons.length,
        buttons: buttons.map((el, i) => ({
          i,
          text: (el.innerText || el.textContent || '').trim(),
          title: el.getAttribute('title') || '',
          cls: (el.className || '').toString(),
          disabled: Boolean(el.disabled)
        }))
      };
    }
    button.click();
    return {
      ok: true,
      headerText,
      index,
      text: (button.innerText || button.textContent || '').trim(),
      title: button.getAttribute('title') || '',
      cls: (button.className || '').toString(),
      disabled: Boolean(button.disabled)
    };
  })()`);
}

async function sleep(client, ms) {
  return client.evaluate(`(() => new Promise((resolve) => setTimeout(resolve, ${Number(ms)})))()`, {
    awaitPromise: true,
  });
}

async function setDiagnosticsService(client, serviceName) {
  return client.evaluate(`(() => {
    const wanted = ${jsString(serviceName)};
    const labels = [...document.querySelectorAll('label')];
    const label = labels.find((el) => (el.innerText || el.textContent || '').trim() === 'Служба для диагностики');
    const root = label ? label.closest('.input-label-container, .row, .p-float-label, .input-wrapper') : null;
    const trigger = root ? root.querySelector('.p-select-label, .p-dropdown-label, .p-select') : document.querySelector('.p-select');
    if (!trigger) {
      return { ok: false, reason: 'diagnostics select trigger not found', wanted };
    }
    trigger.click();

    const options = [...document.querySelectorAll('.p-select-option, .p-dropdown-item, li[role="option"]')];
    const option = options.find((el) => {
      const text = (el.innerText || el.textContent || '').trim();
      return text.toLowerCase().includes(wanted.toLowerCase());
    });
    if (!option) {
      return {
        ok: false,
        reason: 'diagnostics option not found',
        wanted,
        options: options.map((el) => (el.innerText || el.textContent || '').trim()).filter(Boolean)
      };
    }
    option.click();
    return { ok: true, wanted, selected: (option.innerText || option.textContent || '').trim() };
  })()`);
}

async function openConsole(client) {
  return client.evaluate(`(() => new Promise(async (resolve) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    if (!document.querySelector('.console')) {
      const button = document.querySelectorAll('.panel .utility-buttons .btn')[0];
      if (!button) {
        resolve({ ok: false, reason: 'console panel button not found', route: location.hash });
        return;
      }
      button.click();
      await sleep(300);
    }
    resolve({
      ok: true,
      route: location.hash,
      consoleOpen: Boolean(document.querySelector('.console'))
    });
  }))()`, { awaitPromise: true });
}

async function readConsole(client) {
  return client.evaluate(`(() => {
    const items = [...document.querySelectorAll('.console .item')].map((item, index) => ({
      index,
      time: (item.querySelector('.item-title')?.innerText || '').trim(),
      command: (item.querySelector('.item-command')?.innerText || '').trim(),
      response: (item.querySelector('.item-response')?.innerText || '').trim(),
      isError: item.classList.contains('_error')
    }));
    return {
      route: location.hash,
      consoleOpen: Boolean(document.querySelector('.console')),
      count: items.length,
      items
    };
  })()`);
}

async function openSettings(client) {
  return client.evaluate(`(() => new Promise(async (resolve) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    if (!document.querySelector('#host-input')) {
      const button = document.querySelectorAll('.panel .utility-buttons .btn')[1];
      if (!button) {
        resolve({ ok: false, reason: 'settings panel button not found', route: location.hash });
        return;
      }
      button.click();
      await sleep(300);
    }
    resolve({
      ok: true,
      route: location.hash,
      hostInputPresent: Boolean(document.querySelector('#host-input')),
      dialogTitle: [...document.querySelectorAll('.p-dialog-title, .p-dialog-header')]
        .map((el) => (el.innerText || el.textContent || '').trim())
        .find(Boolean) || ''
    });
  }))()`, { awaitPromise: true });
}

async function closeSettings(client) {
  return client.evaluate(`(() => new Promise(async (resolve) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const fireClick = (el) => {
      for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
        el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
      }
    };
    const findSettingsDialog = () => {
      const dialogs = [...document.querySelectorAll('.p-dialog')];
      return dialogs.find((el) => {
        const text = (el.innerText || el.textContent || '');
        const style = window.getComputedStyle(el);
        const visible = style.display !== 'none' && style.visibility !== 'hidden' && style.pointerEvents !== 'none';
        return text.includes('Настройки SSH') && visible;
      }) || null;
    };
    const waitUntilClosed = async (limit = 12) => {
      let stillOpen = true;
      let checks = 0;
      for (; checks < limit; checks += 1) {
        await sleep(100);
        stillOpen = Boolean(findSettingsDialog());
        if (!stillOpen) {
          break;
        }
      }
      return { stillOpen, checks };
    };

    const dialog = findSettingsDialog();
    if (!dialog) {
      resolve({ ok: true, wasOpen: false });
      return;
    }
    const closeButton = dialog.querySelector('.p-dialog-header-close-button, .p-dialog-close-button');
    if (!closeButton) {
      resolve({ ok: false, wasOpen: true, reason: 'close button not found' });
      return;
    }

    const attempts = [];

    fireClick(closeButton);
    let result = await waitUntilClosed(12);
    attempts.push({ method: 'header-fireClick', ...result });

    if (result.stillOpen) {
      closeButton.click();
      result = await waitUntilClosed(12);
      attempts.push({ method: 'header-native-click', ...result });
    }

    if (result.stillOpen) {
      const panelButton = document.querySelectorAll('.panel .utility-buttons .btn')[1] || null;
      if (panelButton) {
        fireClick(panelButton);
        result = await waitUntilClosed(12);
        attempts.push({ method: 'panel-toggle-fireClick', ...result });
      }
    }

    if (result.stillOpen) {
      const panelButton = document.querySelectorAll('.panel .utility-buttons .btn')[1] || null;
      if (panelButton) {
        panelButton.click();
        result = await waitUntilClosed(12);
        attempts.push({ method: 'panel-toggle-native-click', ...result });
      }
    }

    resolve({
      ok: !result.stillOpen,
      wasOpen: true,
      closeMethod: attempts.find((item) => item.stillOpen === false)?.method || null,
      stillOpen: result.stillOpen,
      checks: attempts.reduce((sum, item) => sum + item.checks, 0),
      attempts,
      hostInputPresentAfterClose: Boolean(document.querySelector('#host-input'))
    });
  }))()`, { awaitPromise: true });
}

async function readConnectionForm(client) {
  return client.evaluate(`(() => {
    const dialog = document.querySelector('.p-dialog');
    const host = dialog ? dialog.querySelector('#host-input') : null;
    const key = dialog ? dialog.querySelector('input.key-input') : null;
    const textInputs = dialog ? [...dialog.querySelectorAll('input[type="text"]')] : [];
    const user = textInputs[2] || null;
    const password = textInputs[3] || null;
    const port = textInputs[4] || null;
    return {
      route: location.hash,
      host: host ? host.value : null,
      key: key ? key.value : null,
      user: user ? user.value : null,
      password: password ? password.value : null,
      port: port ? port.value : null,
      connectButtonText: ([...document.querySelectorAll('button')]
        .find((el) => ['Подключиться', 'Отключиться'].includes((el.innerText || el.textContent || '').trim()))
        ?.innerText || '').trim()
    };
  })()`);
}

async function connectMinimal(client) {
  const formState = await readConnectionForm(client);
  if (!formState.host) {
    await openSettings(client);
  }

  return client.evaluate(`(() => new Promise(async (resolve) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const setInput = (el, value) => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      el.focus();
      setter.call(el, value);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    };

    const dialog = document.querySelector('.p-dialog');
    const host = dialog ? dialog.querySelector('#host-input') : null;
    const key = dialog ? dialog.querySelector('input.key-input') : null;
    const textInputs = dialog ? [...dialog.querySelectorAll('input[type="text"]')] : [];
    const user = textInputs[2] || null;
    const password = textInputs[3] || null;
    const port = textInputs[4] || null;

    if (!host || !key || !user || !password || !port) {
      resolve({ ok: false, reason: 'connection form fields not found', route: location.hash });
      return;
    }

    for (const el of [host, key, user, password, port]) {
      setInput(el, '');
      await sleep(150);
    }

    setInput(host, '192.168.122.10');
    await sleep(200);
    setInput(key, '/home/ant/IdeaProjects/configurator/passgen/vcont_initial_access');
    await sleep(200);
    setInput(user, 'service');
    await sleep(200);
    setInput(password, '');
    await sleep(200);
    setInput(port, '22');
    await sleep(300);

    const connectButton = [...document.querySelectorAll('button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Подключиться');
    const disconnectButton = [...document.querySelectorAll('button')]
      .find((el) => (el.innerText || el.textContent || '').trim() === 'Отключиться');

    if (connectButton) {
      connectButton.click();
      await sleep(1200);
    } else if (disconnectButton) {
      resolve({
        ok: true,
        route: location.hash,
        host: host.value,
        key: key.value,
        user: user.value,
        password: password.value,
        port: port.value,
        statusText: 'connected',
        skippedClick: true
      });
      return;
    } else {
      resolve({ ok: false, reason: 'connect/disconnect button not found', route: location.hash });
      return;
    }

    resolve({
      ok: true,
      route: location.hash,
      host: host.value,
      key: key.value,
      user: user.value,
      password: password.value,
      port: port.value,
      statusText: document.body.innerText.includes('Статус: подключен') ? 'connected' : (
        document.body.innerText.includes('Статус: отключен') ? 'disconnected' : 'unknown'
      )
    });
  }))()`, { awaitPromise: true });
}

async function ensureConnectedAndClean(client) {
  const connectResult = await connectMinimal(client);
  const closeSettingsResult = await closeSettings(client);
  return { connectResult, closeSettingsResult };
}

function getSafeActionCatalog() {
  return Object.entries(SAFE_ACTIONS).map(([key, value]) => ({
    key,
    route: value.route,
    risk: value.risk,
    command: value.command,
    collect: value.collect,
  }));
}

async function collectActionState(client, collectMode) {
  if (collectMode === "tables") {
    return readTables(client);
  }
  return snapshot(client);
}

async function runSafeAction(client, actionKey) {
  const action = SAFE_ACTIONS[actionKey];
  if (!action) {
    return {
      ok: false,
      reason: "unknown safe action",
      actionKey,
      knownActions: Object.keys(SAFE_ACTIONS),
    };
  }

  const { connectResult, closeSettingsResult } = await ensureConnectedAndClean(client);
  const routeState = await gotoRoute(client, action.route);
  await openConsole(client);
  const beforeConsole = await readConsole(client);

  let prepareResult = null;
  if (action.prepare?.type === "diagnostics-service") {
    prepareResult = await setDiagnosticsService(client, action.prepare.value);
    await sleep(client, 250);
  }

  let triggerResult = null;
  if (action.trigger.type === "text") {
    triggerResult = await clickTextNth(client, action.trigger.value, action.trigger.nth || 0);
  } else if (action.trigger.type === "title") {
    triggerResult = await clickTitle(client, action.trigger.value);
  } else if (action.trigger.type === "accordion-index") {
    triggerResult = await clickAccordionButtonIndex(client, action.trigger.accordion, action.trigger.value);
  } else if (action.trigger.type === "page-index") {
    triggerResult = await clickPageButtonIndex(client, action.trigger.value);
  } else if (action.trigger.type === "index") {
    triggerResult = await clickButtonIndex(client, action.trigger.value);
  } else {
    return { ok: false, reason: "unsupported trigger type", actionKey, trigger: action.trigger };
  }

  await sleep(client, 1200);

  const afterConsole = await readConsole(client);
  const state = await collectActionState(client, action.collect);
  const newItems = afterConsole.items.slice(beforeConsole.count);
  const matchedItem = [...newItems].reverse().find((item) => item.command === action.command) || null;

  return {
    ok: Boolean(triggerResult?.ok),
    actionKey,
    route: routeState.route,
    risk: action.risk,
    expectedCommand: action.command,
    connectResult,
    closeSettingsResult,
    prepareResult,
    triggerResult,
    consoleDeltaCount: newItems.length,
    matchedCommand: matchedItem ? matchedItem.command : null,
    matchedItem,
    state,
  };
}

async function assertCommand(client, actionKey) {
  const result = await runSafeAction(client, actionKey);
  const matched = Boolean(result.matchedItem);
  return {
    ok: result.ok && matched,
    actionKey,
    route: result.route,
    expectedCommand: result.expectedCommand,
    matched,
    matchedItem: result.matchedItem,
    consoleDeltaCount: result.consoleDeltaCount,
    triggerResult: result.triggerResult,
    prepareResult: result.prepareResult,
  };
}

function inventorySafeRoutes() {
  const groups = {};
  for (const [key, action] of Object.entries(SAFE_ACTIONS)) {
    if (!groups[action.route]) {
      groups[action.route] = [];
    }
    groups[action.route].push({
      key,
      risk: action.risk,
      command: action.command,
      collect: action.collect,
    });
  }

  return {
    count: Object.keys(SAFE_ACTIONS).length,
    routes: Object.entries(groups)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([route, actions]) => ({
        route,
        actions: actions.sort((a, b) => a.key.localeCompare(b.key)),
      })),
  };
}

async function run() {
  const [, , command, ...args] = process.argv;
  if (!command) {
    console.error(
      "Usage: sshcfg_cdp.js <list-elements|goto|snapshot|read-tables|read-selections|read-network-files-state|read-keys-state|read-vm-xmls-state|read-vm-images-state|open-console|read-console|open-settings|read-connection-form|set-host|click-connect|click-text|click-title|connect-minimal|select-app-row|select-prime-row|select-network-file|prepare-network-file-rename|select-first-key|delete-selected-key|select-xml-file|select-image-file|list-safe-actions|run-safe-action|assert-command|inventory-safe-routes> [args]",
    );
    process.exit(2);
  }

  const result = await withClient(async (client) => {
    if (command === "list-elements") return listElements(client);
    if (command === "snapshot") return snapshot(client);
    if (command === "read-tables") return readTables(client);
    if (command === "open-console") return openConsole(client);
    if (command === "read-console") return readConsole(client);
    if (command === "open-settings") return openSettings(client);
    if (command === "read-connection-form") return readConnectionForm(client);
    if (command === "read-selections") return readSelections(client);
    if (command === "read-network-files-state") return readNetworkFilesState(client);
    if (command === "read-keys-state") return readKeysState(client);
    if (command === "read-vm-xmls-state") return readVmFileListState(client, "xml");
    if (command === "read-vm-images-state") return readVmFileListState(client, "images");

    if (command === "goto") {
      const route = args[0];
      if (!route) throw new Error("goto requires a route");
      return gotoRoute(client, route);
    }

    if (command === "set-host") {
      const host = args[0];
      if (!host) throw new Error("set-host requires a value");
      return setHost(client, host);
    }

    if (command === "click-connect") {
      return clickText(client, "Подключиться");
    }

    if (command === "click-text") {
      const text = args.join(" ").trim();
      if (!text) throw new Error("click-text requires button text");
      return clickText(client, text);
    }

    if (command === "click-title") {
      const title = args.join(" ").trim();
      if (!title) throw new Error("click-title requires button title");
      return clickTitle(client, title);
    }

    if (command === "connect-minimal") {
      return connectMinimal(client);
    }

    if (command === "select-app-row") {
      const rowText = args[0];
      const tableIndex = args[1] ? Number(args[1]) : 0;
      if (!rowText) throw new Error("select-app-row requires row text");
      return selectAppTableRow(client, rowText, tableIndex);
    }

    if (command === "select-prime-row") {
      const rowText = args[0];
      const tableIndex = args[1] ? Number(args[1]) : 0;
      if (!rowText) throw new Error("select-prime-row requires row text");
      return selectPrimeTableRow(client, rowText, tableIndex);
    }

    if (command === "select-network-file") {
      const fileName = args[0];
      if (!fileName) throw new Error("select-network-file requires file name");
      return selectNetworkFile(client, fileName);
    }

    if (command === "prepare-network-file-rename") {
      const fileName = args[0];
      const newName = args[1];
      if (!fileName || !newName) throw new Error("prepare-network-file-rename requires fileName and newName");
      return prepareNetworkFileRename(client, fileName, newName);
    }

    if (command === "select-first-key") {
      return selectFirstKey(client);
    }

    if (command === "delete-selected-key") {
      return deleteSelectedKey(client);
    }

    if (command === "select-xml-file") {
      const fileName = args[0];
      if (!fileName) throw new Error("select-xml-file requires file name");
      return selectVmXmlFile(client, fileName);
    }

    if (command === "select-image-file") {
      const fileName = args[0];
      if (!fileName) throw new Error("select-image-file requires file name");
      return selectVmImageFile(client, fileName);
    }

    if (command === "list-safe-actions") {
      return getSafeActionCatalog();
    }

    if (command === "inventory-safe-routes") {
      return inventorySafeRoutes();
    }

    if (command === "run-safe-action") {
      const actionKey = args[0];
      if (!actionKey) throw new Error("run-safe-action requires action key");
      return runSafeAction(client, actionKey);
    }

    if (command === "assert-command") {
      const actionKey = args[0];
      if (!actionKey) throw new Error("assert-command requires action key");
      return assertCommand(client, actionKey);
    }

    throw new Error(`Unknown command: ${command}`);
  });

  printJson(result);
}

run().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
