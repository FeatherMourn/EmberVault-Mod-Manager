import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1120
    height: 720
    title: "EmberVault Mod Manager"
    color: "#0d0c14"

    property color ink: "#edeaf4"
    property color muted: "#918da4"
    property color ember: "#ef8b4d"
    property var packageRecords: passportFixture || []
    property var filteredRecords: packageRecords
    property var selectedRecord: filteredRecords.length > 0 ? filteredRecords[0] : ({})
    property string compatibilityState: deriveCompatibility(selectedRecord)
    property string integrityState: deriveIntegrity(selectedRecord)
    property string backupReadiness: selectedRecord.review_state === "valid" ? "ready" : "review-required"
    property string recoverySummary: selectedRecord.review_state === "valid" ? "No recovery gaps supplied." : "Review recovery evidence before approval."
    property bool approvalGranted: false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 32
        spacing: 16
        Text { text: "MOD MANAGER"; color: ember; font.pixelSize: 11; font.letterSpacing: 1.4 }
        Text { text: "Passport research workspace"; color: ink; font.pixelSize: 30; font.bold: true }
        Text { text: "Offline-first, read-only review. Package actions, runtime hooks, and live-game operations are disabled."; color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            TextField { id: search; placeholderText: "Search package, build, target, or dependency"; Layout.fillWidth: true; onTextChanged: refreshResults() }
            ComboBox { id: buildFilter; model: ["All builds", "1076226", "1077000"]; onActivated: refreshResults() }
            ComboBox { id: targetFilter; model: ["All targets", "client", "dedicated-server"]; onActivated: refreshResults() }
            Label { text: "READ-ONLY"; color: ember }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true; color: "#15141e"; radius: 8
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 16
                    Text { text: "Passport inventory"; color: ink; font.bold: true; font.pixelSize: 18 }
                    Text { text: packageRecords.length === 0 ? "Supply Passport metadata to begin review." : packageRecords.length + " records"; color: muted }
                    ListView {
                        Layout.fillWidth: true; Layout.fillHeight: true; model: filteredRecords
                        delegate: Rectangle {
                            width: ListView.view.width; height: 42; color: modelData === selectedRecord ? "#25202d" : "transparent"
                            Text { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; text: modelData.package_id + " · " + modelData.version + " · " + modelData.review_state; color: ink }
                            MouseArea { anchors.fill: parent; onClicked: selectedRecord = modelData }
                        }
                    }
                }
            }
            Rectangle {
                Layout.preferredWidth: 360; Layout.fillHeight: true; color: "#15141e"; radius: 8
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 16; spacing: 10
                    Text { text: "Review status"; color: ink; font.bold: true; font.pixelSize: 18 }
                    Text { text: "Selected: " + (selectedRecord.package_id || "none"); color: ink }
                    Text { text: "Review state: " + (selectedRecord.review_state || "unknown"); color: ember }
                    Text { text: "Builds: " + (selectedRecord.builds || []).join(", "); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Targets: " + (selectedRecord.targets || []).join(", "); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Dependencies: " + (selectedRecord.dependencies || []).join(", ") || "none"; color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "SHA-256: " + ((selectedRecord.files || []).length > 0 ? selectedRecord.files[0].sha256 : "not supplied"); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Provenance: " + JSON.stringify(selectedRecord.provenance || {}); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Evidence: " + JSON.stringify(selectedRecord.evidence || []); color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Compatibility: " + compatibilityState; color: muted }
                    Text { text: "Integrity: " + integrityState; color: muted }
                    Text { text: "Evidence: provenance and limitations"; color: muted }
                    Text { text: "Save Manager: " + backupReadiness; color: muted }
                    Text { text: "Troubleshooter: " + recoverySummary; color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Text { text: "Control Center: approval " + (approvalGranted ? "granted" : "not granted"); color: ember; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Item { Layout.fillHeight: true }
                    Text { text: "No install, enable, disable, update, or runtime actions are available."; color: muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }
    }

    function refreshResults() {
        var query = search.text.toLowerCase()
        var build = buildFilter.currentText === "All builds" ? "" : buildFilter.currentText
        var target = targetFilter.currentText === "All targets" ? "" : targetFilter.currentText
        filteredRecords = packageRecords.filter(function (record) {
            var haystack = JSON.stringify(record).toLowerCase()
            return (!query || haystack.indexOf(query) >= 0) &&
                   (!build || (record.builds || []).indexOf(build) >= 0) &&
                   (!target || (record.targets || []).indexOf(target) >= 0)
        })
        selectedRecord = filteredRecords.length > 0 ? filteredRecords[0] : ({})
    }

    function deriveCompatibility(record) {
        if (!record || !record.builds || !record.targets || record.builds.length === 0 || record.targets.length === 0)
            return "unknown"
        return record.review_state === "valid" ? "verified" : (record.review_state === "partial" ? "partial" : "review-required")
    }

    function deriveIntegrity(record) {
        if (!record || !record.files || record.files.length === 0) return "not supplied"
        var digest = record.files[0].sha256 || ""
        return digest.length === 64 ? (record.review_state === "valid" ? "verified" : "review-required") : "invalid"
    }
}
