<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-4 py-4">
      <div class="max-w-5xl mx-auto flex items-center gap-3">
        <div class="flex flex-col">
          <h1 class="text-xl font-bold text-gray-900 leading-tight">
            Listas Venezuela
          </h1>
          <p class="text-sm text-gray-500">
            Convierte listas hospitalarias en CSV para hospitalesenvenezuela.com
          </p>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <!-- Step 1: Upload -->
      <section v-if="step === 'upload'">
        <h2 class="text-base font-semibold text-gray-700 mb-4">
          1. Sube las fotos de las listas
        </h2>

        <div
          class="border-2 border-dashed rounded-xl p-10 text-center transition-colors"
          :class="
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white hover:border-gray-400'
          "
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/heic"
            multiple
            class="hidden"
            @change="onFileSelected"
          />

          <div v-if="previews.length === 0" class="space-y-3">
            <div class="text-4xl text-gray-300">📷</div>
            <p class="text-gray-600 text-sm">
              Arrastra las fotos aquí o
              <button
                class="text-blue-600 underline font-medium"
                @click="fileInput?.click()"
              >
                selecciona archivos
              </button>
            </p>
            <p class="text-xs text-gray-400">
              Puedes subir varias a la vez · JPG, PNG, WEBP o HEIC · máx. 10 MB
              c/u
            </p>
          </div>

          <div v-else class="space-y-4">
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="(p, i) in previews" :key="p.url" class="relative">
                <img
                  :src="p.url"
                  :alt="p.name"
                  class="h-28 w-full object-cover rounded-lg shadow"
                />
                <button
                  class="absolute -top-2 -right-2 bg-white text-gray-500 hover:text-red-500 border border-gray-300 rounded-full w-6 h-6 flex items-center justify-center shadow"
                  title="Quitar"
                  @click="removeFile(i)"
                >
                  ✕
                </button>
                <p class="truncate text-xs text-gray-400 mt-1">{{ p.name }}</p>
              </div>
            </div>
            <button
              class="text-sm text-blue-600 underline font-medium"
              @click="fileInput?.click()"
            >
              + Agregar más fotos
            </button>
          </div>
        </div>

        <div v-if="previews.length > 0" class="mt-4 space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Centro de salud (opcional, aplica a todas las fotos)
            </label>
            <input
              v-model="centroHint"
              type="text"
              placeholder="Ej: Hospital Central de Caracas"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            :disabled="isProcessing"
            class="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            @click="processImages"
          >
            <span
              v-if="isProcessing"
              class="flex items-center justify-center gap-2"
            >
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                />
              </svg>
              {{ processingStatus }}
            </span>
            <span v-else>
              Procesar {{ selectedFiles.length }}
              {{ selectedFiles.length === 1 ? "lista" : "listas" }}
            </span>
          </button>
        </div>

        <p
          v-if="uploadError"
          class="mt-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3"
        >
          {{ uploadError }}
        </p>
      </section>

      <!-- Step 2: Review table -->
      <section v-if="step === 'review'">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-base font-semibold text-gray-700">
              2. Revisa y corrige los datos
            </h2>
            <p class="text-sm text-gray-500 mt-0.5">
              {{ records.length }} persona(s) encontradas · haz clic en
              cualquier celda para editar
            </p>
          </div>
          <button
            class="text-sm text-gray-500 underline hover:text-gray-700"
            @click="resetAll"
          >
            Subir otra imagen
          </button>
        </div>

        <!-- Table -->
        <div
          class="bg-white rounded-xl border border-gray-200 overflow-x-auto shadow-sm"
        >
          <table class="min-w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 bg-gray-50">
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide w-8"
                >
                  #
                </th>
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  Nombre
                </th>
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  Apellido
                </th>
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  Cédula
                </th>
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  Centro
                </th>
                <th
                  class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  Edad / Sector
                </th>
                <th class="px-3 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in records"
                :key="row.id ?? i"
                class="border-b border-gray-100 last:border-0 hover:bg-gray-50"
              >
                <td class="px-3 py-2 text-gray-400 text-xs">{{ i + 1 }}</td>
                <td class="px-1 py-1">
                  <input
                    v-model="row.nombre"
                    class="w-full px-2 py-1.5 rounded border border-transparent focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-transparent hover:bg-white hover:border-gray-300 transition-colors"
                    :class="{ 'border-red-300 bg-red-50': !row.nombre }"
                  />
                </td>
                <td class="px-1 py-1">
                  <input
                    v-model="row.apellido"
                    class="w-full px-2 py-1.5 rounded border border-transparent focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-transparent hover:bg-white hover:border-gray-300 transition-colors"
                    :class="{ 'border-red-300 bg-red-50': !row.apellido }"
                  />
                </td>
                <td class="px-1 py-1">
                  <input
                    v-model="row.cedula"
                    class="w-full px-2 py-1.5 rounded border border-transparent focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-transparent hover:bg-white hover:border-gray-300 transition-colors font-mono"
                  />
                </td>
                <td class="px-1 py-1">
                  <input
                    v-model="row.centro"
                    class="w-full px-2 py-1.5 rounded border border-transparent focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-transparent hover:bg-white hover:border-gray-300 transition-colors"
                    :class="{ 'border-red-300 bg-red-50': !row.centro }"
                  />
                </td>
                <td class="px-1 py-1">
                  <input
                    v-model="row.edad_sector"
                    class="w-full px-2 py-1.5 rounded border border-transparent focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-transparent hover:bg-white hover:border-gray-300 transition-colors"
                  />
                </td>
                <td class="px-2 py-1">
                  <button
                    class="text-gray-300 hover:text-red-400 transition-colors"
                    title="Eliminar fila"
                    @click="removeRow(i)"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Add row -->
        <button
          class="mt-3 text-sm text-blue-600 hover:text-blue-700 underline"
          @click="addRow"
        >
          + Agregar persona manualmente
        </button>

        <!-- Validation warnings -->
        <div
          v-if="missingApellidoCount > 0"
          class="mt-4 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3"
        >
          {{ missingApellidoCount }} fila(s) sin apellido. El apellido es
          obligatorio: complétalo antes de exportar.
        </div>
        <div
          v-if="omittedCount > 0"
          class="mt-3 text-sm text-gray-600 bg-gray-100 border border-gray-200 rounded-lg px-4 py-3"
        >
          {{ omittedCount }} fila(s) se omitirán del CSV por no tener nombre o
          centro. La cédula y la edad/sector sí pueden quedar vacías.
        </div>

        <!-- Export bar -->
        <div
          class="mt-6 flex flex-col sm:flex-row gap-3 items-start sm:items-center"
        >
          <button
            :disabled="exportableRows.length === 0 || missingApellidoCount > 0"
            class="bg-green-600 text-white font-semibold px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            @click="exportCSV"
          >
            Exportar CSV ({{ exportableRows.length }} registros)
          </button>
          <a
            href="https://hospitalesenvenezuela.com/"
            target="_blank"
            rel="noopener"
            class="text-sm text-blue-600 underline hover:text-blue-700"
          >
            Ir a hospitalesenvenezuela.com →
          </a>
        </div>
      </section>

      <!-- Step 3: Done -->
      <section v-if="step === 'done'" class="text-center py-12 space-y-4">
        <div class="text-5xl">✅</div>
        <h2 class="text-xl font-bold text-gray-800">CSV exportado</h2>
        <p class="text-gray-600 text-sm max-w-sm mx-auto">
          El archivo se ha descargado. Súbelo en
          <a
            href="https://hospitalesenvenezuela.com/"
            target="_blank"
            rel="noopener"
            class="text-blue-600 underline"
          >
            hospitalesenvenezuela.com
          </a>
          para publicar los registros.
        </p>
        <button
          class="mt-4 bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 font-medium"
          @click="resetAll"
        >
          Procesar otra lista
        </button>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useOCR } from "~/composables/useOCR";

type Persona = {
  id?: string;
  nombre: string;
  apellido: string;
  cedula: string;
  centro: string;
  edad_sector: string;
};

const { uploadAndProcess } = useOCR();

const step = ref<"upload" | "review" | "done">("upload");
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFiles = ref<File[]>([]);
const previews = ref<{ name: string; url: string }[]>([]);
const centroHint = ref("");
const isDragging = ref(false);
const isProcessing = ref(false);
const processingStatus = ref("");
const uploadError = ref("");
const records = ref<Persona[]>([]);

// Hard requirement to land in the CSV: nombre + centro. Rows missing either
// are omitted from the export (cédula and edad_sector are optional).
const exportableRows = computed(() =>
  records.value.filter((r) => r.nombre.trim() && r.centro.trim()),
);
// Rows that will be dropped (no nombre or no centro).
const omittedCount = computed(
  () => records.value.length - exportableRows.value.length,
);
// Exportable rows still missing apellido (obligatorio — must be filled to export).
const missingApellidoCount = computed(
  () => exportableRows.value.filter((r) => !r.apellido.trim()).length,
);

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files) loadFiles(input.files);
  input.value = ""; // allow re-selecting the same file
}

function onDrop(e: DragEvent) {
  isDragging.value = false;
  if (e.dataTransfer?.files) loadFiles(e.dataTransfer.files);
}

function loadFiles(fileList: FileList) {
  uploadError.value = "";
  for (const file of Array.from(fileList)) {
    if (!file.type.startsWith("image/")) continue;
    selectedFiles.value.push(file);
    previews.value.push({ name: file.name, url: URL.createObjectURL(file) });
  }
}

function removeFile(i: number) {
  URL.revokeObjectURL(previews.value[i].url);
  selectedFiles.value.splice(i, 1);
  previews.value.splice(i, 1);
}

function resetUpload() {
  previews.value.forEach((p) => URL.revokeObjectURL(p.url));
  selectedFiles.value = [];
  previews.value = [];
  centroHint.value = "";
  uploadError.value = "";
  if (fileInput.value) fileInput.value.value = "";
}

function resetAll() {
  resetUpload();
  records.value = [];
  step.value = "upload";
}

async function processImages() {
  if (selectedFiles.value.length === 0) return;
  isProcessing.value = true;
  uploadError.value = "";

  try {
    const n = selectedFiles.value.length;
    processingStatus.value =
      n === 1 ? "Leyendo imagen…" : `Procesando ${n} imágenes…`;
    const result = await uploadAndProcess(
      selectedFiles.value,
      centroHint.value,
    );
    records.value = result.map((r: Persona) => ({ ...r }));
    step.value = "review";
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Error desconocido";
    uploadError.value = `Error al procesar las imágenes: ${message}`;
  } finally {
    isProcessing.value = false;
    processingStatus.value = "";
  }
}

function addRow() {
  records.value.push({
    nombre: "",
    apellido: "",
    cedula: "",
    centro: "",
    edad_sector: "",
  });
}

function removeRow(i: number) {
  records.value.splice(i, 1);
}

function exportCSV() {
  const headers = ["nombre", "apellido", "cedula", "centro", "edad_sector"];
  // Match the site's template: fields are unquoted unless they contain a
  // comma, quote or newline (then minimal RFC-4180 quoting kicks in).
  const esc = (v: string) => {
    const s = v ?? "";
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = exportableRows.value.map((r) =>
    headers.map((h) => esc(r[h as keyof typeof r] ?? "")).join(","),
  );
  const csv = [headers.join(","), ...rows].join("\n");

  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lista-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  step.value = "done";
}
</script>
