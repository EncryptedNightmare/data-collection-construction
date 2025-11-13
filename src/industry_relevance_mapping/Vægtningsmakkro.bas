Attribute VB_Name = "Module1"
Option Explicit


Private Const UPPER_BOUND As Double = 200

Private Function Del1Score(ByVal v As Variant) As Long
    Dim p As Double

    If Not IsNumeric(v) Then
        Del1Score = 0
        Exit Function
    End If

    Dim x As Double
    x = CDbl(v)

    If x < 50 Or x > UPPER_BOUND Then
        p = 0
    ElseIf x < 125 Then
        ' 50 ? 10  ...  125 ? 40  (stigning)
        p = 10 + (x - 50) * (30 / 75)   ' = 0,4 pr. enhed
    ElseIf x <= 135 Then
        ' Plateau
        p = 40
    Else
        ' 135 ? 40  ...  UPPER_BOUND(=200) ? 10  (fald)
        p = 10 + (UPPER_BOUND - x) * (30 / (UPPER_BOUND - 135))  ' 30/65 ˜ 0,4615
        If p < 0 Then p = 0
    End If

    Del1Score = Round(p, 0)
End Function

Sub BeregnPointAlleRækker()

    Dim ws As Worksheet, wsSum As Worksheet
    Dim rowOut As Long, r As Long, lastRow As Long
    Dim v As Variant, txt As String, txtLower As String
    Dim p1 As Long, p2 As Long, p3 As Long
    Dim hasE As Boolean, hasS As Boolean, hasM As Boolean, n As Long

    ' Find eller opret Oversigt
    On Error Resume Next
    Set wsSum = ThisWorkbook.Worksheets("Vægtning")
    On Error GoTo 0
    If wsSum Is Nothing Then
        Set wsSum = ThisWorkbook.Worksheets.Add(Before:=ThisWorkbook.Worksheets(1))
        wsSum.Name = "Vægtning"
    End If

    ' Ryd og skriv overskrifter
    wsSum.Cells.ClearContents
    wsSum.Range("A1").Value = "Ark"
    wsSum.Range("B1").Value = "Række"
    wsSum.Range("C1").Value = "Tekst fra kolonne D"
    wsSum.Range("D1").Value = "Del 1 (C, gradueret)"
    wsSum.Range("E1").Value = "Del 2 (funktioner i N)"
    wsSum.Range("F1").Value = "Del 3 (kombination i N)"

    rowOut = 2

    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> wsSum.Name Then

            ' Find sidste udfyldte række i C/N
            lastRow = ws.Cells(ws.Rows.Count, "C").End(xlUp).Row
            If ws.Cells(ws.Rows.Count, "N").End(xlUp).Row > lastRow Then
                lastRow = ws.Cells(ws.Rows.Count, "N").End(xlUp).Row
            End If

            For r = 3 To lastRow

                ' --- Del 1 (kolonne C) ---
                v = ws.Cells(r, "C").Value
                p1 = Del1Score(v)

                ' --- Del 2 & 3 (kolonne N) ---
                txt = CStr(ws.Cells(r, "N").Value)
                txtLower = LCase$(txt)

                hasE = (InStr(1, txtLower, "entreprise", vbTextCompare) > 0)
                hasS = (InStr(1, txtLower, "service", vbTextCompare) > 0)
                hasM = (InStr(1, txtLower, "små opgaver", vbTextCompare) > 0)

                n = 0
                If hasE Then n = n + 1
                If hasS Then n = n + 1
                If hasM Then n = n + 1

                ' Del 2: 3/2/1 = 40/25/10 (0 hvis ingen)
                Select Case n
                    Case 3: p2 = 40
                    Case 2: p2 = 25
                    Case 1: p2 = 10
                    Case Else: p2 = 0
                End Select

                ' Del 3: kombinationsregel
                If n = 0 Then
                    p3 = 0
                ElseIf hasE And hasS Then
                    p3 = 20
                ElseIf (Not hasE And Not hasS And hasM) Then
                    p3 = 5
                Else
                    p3 = 10
                End If

                ' --- Skriv i Oversigt ---
                wsSum.Cells(rowOut, 1).Value = ws.Name
                wsSum.Cells(rowOut, 2).Value = r
                wsSum.Cells(rowOut, 3).Value = ws.Cells(r, "D").Value
                wsSum.Cells(rowOut, 4).Value = p1
                wsSum.Cells(rowOut, 5).Value = p2
                wsSum.Cells(rowOut, 6).Value = p3

                rowOut = rowOut + 1
            Next r
        End If
    Next ws

    MsgBox "Færdig! Del 1 er nu gradueret 50?125 (op), 125–135 (40), 135?200 (ned)."
End Sub

