let table;
let paperData = [];

async function loadPapers() {
    const response = await fetch('./papers.json');
    if (!response.ok) {
        throw new Error('Could not load papers.json');
    }
    return await response.json();
}

function getTagColumns(data) {
    const excluded = new Set(['title', 'authors', 'year', 'venue', 'doi', 'doi_url', 'url', 'abstract']);
    const columns = new Set();

    data.forEach(row => {
        Object.entries(row).forEach(([key, value]) => {
            if (!excluded.has(key) && Array.isArray(value)) {
                columns.add(key);
            }
        });
    });

    const preferredOrder = [
        'specified_audience',
        'role',
        'evaluation_environment',
        'evaluation_measures'
    ];

    return [...columns].sort((a, b) => {
        const aIndex = preferredOrder.indexOf(a);
        const bIndex = preferredOrder.indexOf(b);

        // If both are in preferredOrder, sort by that
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;

        // If only one is in preferredOrder, it comes first
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;

        // Otherwise fallback to alphabetical
        return a.localeCompare(b);
    });
}

function uniqueSortedTags(data, tagColumns) {
    const allTags = data.flatMap(row =>
        tagColumns.flatMap(col => Array.isArray(row[col]) ? row[col] : [])
    );
    return [...new Set(allTags)].sort((a, b) => a.localeCompare(b));
}

function formatLabel(key) {
  const formatted = key
    .split("_")
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

  if (key === "role") {
    return formatted + " of Visualization";
  }

  return formatted;
}

function uniqueSortedTagsForColumn(data, column) {
  const tags = data.flatMap(row => Array.isArray(row[column]) ? row[column] : []);
  return [...new Set(tags)].sort((a, b) => a.localeCompare(b));
}

function populateGroupedFilters(tagColumns, data) {
  const container = document.getElementById("groupedFilters");
  container.innerHTML = "";

  tagColumns.forEach(column => {
    const wrapper = document.createElement("div");
    wrapper.className = "field grouped-filter";

    const label = document.createElement("label");
    label.textContent = formatLabel(column);

    const box = document.createElement("div");
    box.className = "checkbox-group";
    box.dataset.column = column;

    uniqueSortedTagsForColumn(data, column).forEach((tag, index) => {
      const item = document.createElement("label");
      item.className = "checkbox-option";

      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = tag;
      input.dataset.column = column;
      input.id = `filter-${column}-${index}`;
      input.addEventListener("change", applyFilters);

      const text = document.createElement("span");
      text.textContent = tag;

      item.appendChild(input);
      item.appendChild(text);
      box.appendChild(item);
    });

    wrapper.appendChild(label);
    wrapper.appendChild(box);
    container.appendChild(wrapper);
  });
}

function getSelectedTagsByColumn() {
  const selected = {};
  const groups = document.querySelectorAll(".checkbox-group");

  groups.forEach(group => {
    const column = group.dataset.column;
    selected[column] = Array.from(
      group.querySelectorAll('input[type="checkbox"]:checked')
    ).map(input => input.value);
  });

  return selected;
}

function getSelectedTags() {
    const select = document.getElementById('tagFilter');
    return Array.from(select.selectedOptions).map(option => option.value);
}

function matchesKeyword(row, keyword) {
    if (!keyword) return true;

    const excluded = new Set(['title', 'authors', 'year', 'venue', 'doi', 'doi_url', 'url', 'abstract']);
    const tagValues = Object.entries(row)
        .filter(([key, value]) => !excluded.has(key) && Array.isArray(value))
        .flatMap(([, value]) => value);

    const haystack = [
        row.title,
        row.authors,
        row.venue,
        String(row.year ?? ''),
        row.abstract,
        row.doi,
        ...tagValues
    ]
        .join(' ')
        .toLowerCase();

    return haystack.includes(keyword.toLowerCase());
}

function matchesTagsByColumn(row, selectedTagsByColumn) {
  return Object.entries(selectedTagsByColumn).every(([column, selectedTags]) => {
    if (!selectedTags.length) return true;
    const rowTags = Array.isArray(row[column]) ? row[column] : [];
    return selectedTags.some(tag => rowTags.includes(tag));
  });
}

function applyFilters() {
  const keyword = document.getElementById("keywordInput").value.trim();
  const selectedTagsByColumn = getSelectedTagsByColumn();

  const filtered = paperData.filter(row => {
    return matchesKeyword(row, keyword) &&
           matchesTagsByColumn(row, selectedTagsByColumn);
  });

  table.setData(filtered);
  document.getElementById("rowCount").textContent = filtered.length;
}

function renderTable(data) {
    table = new Tabulator('#papers-table', {
        data,
        layout: 'fitColumns',
        responsiveLayout: 'collapse',
        pagination: true,
        paginationSize: 12,
        movableColumns: false,
        resizableRows: false,
        initialSort: [{ column: 'year', dir: 'desc' }],
        columns: [
            {
                title: 'Title',
                field: 'title',
                minWidth: 280,
                formatter(cell) {
                    const row = cell.getRow().getData();
                    const title = row.title || '';
                    const url = row.url || row.doi_url || null;
                    if (url) {
                        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`;
                    }
                    return title;
                }
            },
            {
                title: 'Authors',
                field: 'authors',
                headerSort: false,
                minWidth: 220
            },
            {
                title: 'Year',
                field: 'year',
                width: 95,
                hozAlign: 'center'
            },
            {
                title: 'Venue',
                field: 'venue',
                minWidth: 140
            },
            // {
            //     title: 'Tags',
            //     field: 'all_tags',
            //     minWidth: 260,
            //     formatter(cell) {
            //         const row = cell.getRow().getData();
            //         const tags = Object.entries(row)
            //             .filter(([, value]) => Array.isArray(value))
            //             .flatMap(([, value]) => value);
            //         return [...new Set(tags)]
            //             .map(tag => `<span style="display:inline-block;margin:2px 6px 2px 0;padding:3px 8px;border-radius:999px;background:#f3f4f6;font-size:0.75rem;">${tag}</span>`)
            //             .join('');
            //     }
            // },
            {
                title: 'DOI',
                field: 'doi',
                minWidth: 170,
                formatter(cell) {
                    const doi = cell.getValue();
                    if (!doi) return '';
                    const href = doi.startsWith('http') ? doi : `https://doi.org/${doi}`;
                    return `<a href="${href}" target="_blank" rel="noopener noreferrer">${doi}</a>`;
                }
            }
        ]
    });

    document.getElementById('rowCount').textContent = data.length;
}

document.getElementById("keywordInput").addEventListener("input", applyFilters);

document.getElementById("resetFilters").addEventListener("click", () => {
  document.getElementById("keywordInput").value = "";
  document.querySelectorAll('.checkbox-group input[type="checkbox"]').forEach(input => {
    input.checked = false;
  });
  applyFilters();
});

document.getElementById("downloadCSV").addEventListener("click", function () {
  table.download("csv", "filtered_studies.csv");
});

(async function init() {
    try {
        paperData = await loadPapers();
        const tagColumns = getTagColumns(paperData);
        populateGroupedFilters(tagColumns, paperData);
        renderTable(paperData);
    } catch (error) {
        const el = document.getElementById('papers-table');
        el.innerHTML = `
          <div style="padding:16px;border:1px solid #fecaca;background:#fef2f2;border-radius:12px;color:#991b1b;">
            <strong>Could not load the paper table.</strong><br />
            Make sure <code>papers.json</code> exists in the same folder as <code>index.html</code>.
          </div>
        `;
        console.error(error);
    }
})();
